# Development Workflow

## Tool Usage Guidelines

### VS Code (Production Code)
- All C++ implementation
- Python production classes and APIs
- Swift iOS app development
- Configuration files
- Documentation
- Build scripts

### Jupyter Lab (Research & Analysis)
- Strategy backtesting and optimization
- Market data exploration
- ML model development and training
- Performance analysis and visualization
- Quick prototyping and hypothesis testing

## Git Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/feature-name`: Individual features
- `hotfix/issue-name`: Critical bug fixes

### Commit Guidelines
- Commit complete, working features
- Use descriptive commit messages
- Never commit API keys or sensitive data
- Test before committing

### Example Workflow
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/sentiment-analysis

# Development cycle
# ... make changes in VS Code ...
git add .
git commit -m "Implement news sentiment processing"

# Research in Jupyter
# ... experiment with models ...
# Save notebook automatically commits

# Convert research to production code
# ... update VS Code implementation ...
git add .
git commit -m "Optimize sentiment model based on research"

# Complete feature
git checkout develop
git merge feature/sentiment-analysis
git push origin develop
```
