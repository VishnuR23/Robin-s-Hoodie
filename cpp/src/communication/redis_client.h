#pragma once
#include <string>
#include <vector>
#include <iostream>
#include <hiredis/hiredis.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class RedisClient {
private:
    redisContext* context;
    std::string host;
    int port;
    bool connected;
    
public:
    RedisClient(const std::string& redis_host = "localhost", int redis_port = 6379) 
        : host(redis_host), port(redis_port), connected(false) {
        connect();
    }
    
    ~RedisClient() {
        if (context && connected) {
            redisFree(context);
        }
    }
    
    bool connect() {
        context = redisConnect(host.c_str(), port);
        if (context == nullptr || context->err) {
            if (context) {
                std::cerr << "Redis connection error: " << context->errstr << std::endl;
                redisFree(context);
                context = nullptr;
            } else {
                std::cerr << "Can't allocate redis context" << std::endl;
            }
            connected = false;
            return false;
        }
        
        connected = true;
        std::cout << "✅ Connected to Redis at " << host << ":" << port << std::endl;
        return true;
    }
    
    bool isConnected() const {
        return connected;
    }
    
    bool storeStockData(const std::string& symbol, const json& data) {
        if (!connected) {
            std::cerr << "❌ Redis not connected" << std::endl;
            return false;
        }
        
        std::string key = "stock:current:" + symbol;
        std::string json_str = data.dump();
        
        redisReply* reply = (redisReply*)redisCommand(context, "SET %s %s", key.c_str(), json_str.c_str());
        
        if (reply == nullptr) {
            std::cerr << "❌ Redis SET command failed" << std::endl;
            return false;
        }
        
        bool success = (reply->type == REDIS_REPLY_STATUS && std::string(reply->str) == "OK");
        freeReplyObject(reply);
        
        if (success) {
            // Also add to historical data list
            std::string hist_key = "stock:history:" + symbol;
            redisReply* hist_reply = (redisReply*)redisCommand(context, "LPUSH %s %s", hist_key.c_str(), json_str.c_str());
            if (hist_reply) {
                freeReplyObject(hist_reply);
            }
            
            // Keep only last 1000 historical entries
            redisReply* trim_reply = (redisReply*)redisCommand(context, "LTRIM %s 0 999", hist_key.c_str());
            if (trim_reply) {
                freeReplyObject(trim_reply);
            }
            
            std::cout << "💾 Stored " << symbol << " data in Redis" << std::endl;
        }
        
        return success;
    }
    
    bool storeTradingSignal(const std::string& symbol, const std::string& signal, 
                           const std::string& reason, double confidence) {
        if (!connected) return false;
        
        json signal_data = {
            {"symbol", symbol},
            {"signal", signal},
            {"reason", reason},
            {"confidence", confidence},
            {"timestamp", std::time(nullptr)},
            {"source", "cpp_engine"}
        };
        
        std::string key = "signal:latest:" + symbol;
        std::string json_str = signal_data.dump();
        
        redisReply* reply = (redisReply*)redisCommand(context, "SET %s %s", key.c_str(), json_str.c_str());
        
        if (reply == nullptr) return false;
        
        bool success = (reply->type == REDIS_REPLY_STATUS);
        freeReplyObject(reply);
        
        if (success) {
            // Also add to signals stream for Python to process
            std::string stream_key = "signals:stream";
            redisReply* stream_reply = (redisReply*)redisCommand(context, 
                "LPUSH %s %s", stream_key.c_str(), json_str.c_str());
            if (stream_reply) {
                freeReplyObject(stream_reply);
            }
            
            std::cout << "📡 Stored trading signal: " << symbol << " -> " << signal << std::endl;
        }
        
        return success;
    }
    
    std::string getStockData(const std::string& symbol) {
        if (!connected) return "";
        
        std::string key = "stock:current:" + symbol;
        redisReply* reply = (redisReply*)redisCommand(context, "GET %s", key.c_str());
        
        if (reply == nullptr || reply->type != REDIS_REPLY_STRING) {
            if (reply) freeReplyObject(reply);
            return "";
        }
        
        std::string result(reply->str);
        freeReplyObject(reply);
        return result;
    }
    
    bool publishMarketUpdate(const std::string& channel, const json& data) {
        if (!connected) return false;
        
        std::string json_str = data.dump();
        redisReply* reply = (redisReply*)redisCommand(context, "PUBLISH %s %s", 
                                                     channel.c_str(), json_str.c_str());
        
        if (reply == nullptr) return false;
        
        bool success = (reply->type == REDIS_REPLY_INTEGER);
        freeReplyObject(reply);
        
        return success;
    }
    
    std::vector<std::string> getAvailableSymbols() {
        if (!connected) return {};
        
        redisReply* reply = (redisReply*)redisCommand(context, "KEYS stock:current:*");
        std::vector<std::string> symbols;
        
        if (reply && reply->type == REDIS_REPLY_ARRAY) {
            for (size_t i = 0; i < reply->elements; i++) {
                std::string key(reply->element[i]->str);
                // Extract symbol from "stock:current:AAPL" -> "AAPL"
                size_t pos = key.find_last_of(':');
                if (pos != std::string::npos) {
                    symbols.push_back(key.substr(pos + 1));
                }
            }
        }
        
        if (reply) freeReplyObject(reply);
        return symbols;
    }
};