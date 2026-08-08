# GitHub Actions Configuration

This document describes the configuration of GitHub Actions workflows for the Ona SDK project.

## Overview

The GitHub Actions configuration provides a comprehensive CI/CD pipeline for automated testing, linting, security scanning, and deployment validation across both Python and JavaScript components of the SDK.

## Directory Structure

```
.github/
├── workflows/                    # GitHub Actions workflow files
│   ├── _common.yml              # Common configuration shared across workflows
│   ├── _template.yml            # Template for creating new workflows
│   ├── README.md               # Workflow documentation
│   ├── auto-test-criteria.yml   # Existing workflow for test criteria
│   └── [other workflow files]  # Individual workflow configurations
├── permissions.yml              # Permissions configuration
└── CONFIGURATION.md             # This configuration document
```

## Configuration Files

### 1. Common Configuration (`_common.yml`)

Contains shared configuration reused across all workflows:

- **Environment Variables**: Default Python/Node.js versions, repository info
- **Job Defaults**: Timeout settings, environment variables
- **Step Defaults**: Common step configurations
- **Cache Configuration**: Caching strategies for dependencies
- **Artifact Configuration**: Artifact retention and management
- **Notification Configuration**: Failure and success notifications
- **Matrix Strategies**: Python and Node.js version matrices
- **Workflow Permissions**: Default permissions for workflows
- **Concurrency Control**: Workflow concurrency settings
- **Workflow Triggers**: Common trigger patterns

### 2. Permissions Configuration (`permissions.yml`)

Defines permissions for GitHub Actions workflows:

- **Default Permissions**: Base permissions for all workflows
- **Workflow-Specific Permissions**: Custom permissions per workflow type
- **Environment Permissions**: Permissions for different environments
- **Branch Protection**: Integration with branch protection rules
- **Secret Management**: Required and optional secrets
- **Rate Limiting**: Concurrent workflow and job limits
- **Cache Configuration**: Cache expiration and size limits
- **Artifact Management**: Artifact retention and compression
- **Security Configuration**: Code scanning, secret scanning, dependency scanning
- **Compliance**: Approval requirements and audit logging

### 3. Workflow Template (`_template.yml`)

Template for creating new workflows with:

- **Standard Structure**: Setup, main, validate, notify, cleanup jobs
- **Change Detection**: Automatic detection of Python/JavaScript changes
- **Matrix Support**: Built-in support for matrix strategies
- **Artifact Management**: Automatic artifact upload/download
- **Notification System**: Status-based notifications
- **Cleanup**: Resource cleanup and temporary file management

## Workflow Types

### 1. Language-Specific Workflows

**Python CI/CD**:
- Linting with Ruff
- Unit testing with pytest
- Dependency validation
- Test coverage reporting

**JavaScript CI/CD**:
- Linting with ESLint
- Unit testing with Jest
- Dependency validation
- Test coverage reporting

### 2. Integration Workflows

**Cross-Language Integration**:
- API compatibility testing
- Serialization round-trip validation
- Data consistency checks
- Regression test protection

### 3. Quality Assurance Workflows

**Security Scanning**:
- Dependency vulnerability scanning
- Code security analysis
- Secret detection
- Compliance checking

**Performance Monitoring**:
- Performance benchmarking
- Regression detection
- Trend analysis
- Resource usage tracking

**Documentation Validation**:
- Markdown linting
- Code example execution
- API documentation compatibility
- Documentation completeness checking

### 4. Process Workflows

**Pull Request Validation**:
- Automatic validation on PR events
- Status check integration
- Merge blocking for failed validations
- Multi-component validation

## Configuration Management

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `PYTHON_VERSION` | Default Python version | "3.11" |
| `NODE_VERSION` | Default Node.js version | "20" |
| `REPO_NAME` | Repository name | `${{ github.repository }}` |
| `BRANCH_NAME` | Current branch name | `${{ github.ref_name }}` |
| `CACHE_PREFIX` | Cache key prefix | `ci-cache-${{ github.run_id }}` |
| `ARTIFACT_RETENTION_DAYS` | Artifact retention period | 7 |

### Cache Configuration

Caching is configured to improve workflow performance:

- **Python Cache**: `~/.cache/pip`, `~/.local/share/virtualenvs`
- **JavaScript Cache**: `javascript/node_modules`, `~/.npm`
- **General Cache**: `~/.cache`, `/tmp/gh-actions`
- **Expiration**: 7 days
- **Maximum Size**: 1024 MB

### Artifact Management

Artifacts are automatically managed with:

- **Retention Period**: 7 days by default
- **Maximum Size**: 500 MB per artifact
- **Compression**: Enabled for logs and test results
- **Types Retained**: Test reports, coverage data, security reports

## Security Configuration

### Secret Scanning

Automated secret scanning with patterns for:
- AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- GitHub tokens (`GITHUB_TOKEN`)
- Third-party service tokens (`SLACK_WEBHOOK_URL`, `SNYK_TOKEN`)

### Dependency Scanning

Regular scanning of dependencies for vulnerabilities:
- **Python**: Safety, pip-audit
- **JavaScript**: npm audit, Snyk
- **Frequency**: Daily scheduled scans + on push

### Code Scanning

Static code analysis with:
- **CodeQL**: Advanced code analysis
- **ESLint Security**: JavaScript security rules
- **Bandit**: Python security analysis

## Branch Protection Integration

The configuration integrates with GitHub branch protection rules:

### Main Branch
- Required status checks for all core workflows
- Required pull request reviews (1 approval minimum)
- Linear history enforcement
- No force pushes allowed

### Develop Branch
- Required status checks for language workflows
- Required pull request reviews
- No force pushes allowed

## Notification System

### Notification Channels
- **GitHub**: Native GitHub notifications
- **Slack**: Optional Slack integration
- **Email**: Email summaries for stakeholders
- **Webhook**: Custom webhook integration

### Notification Triggers
- **On Failure**: Immediate notification
- **On Success**: Only after previous failure
- **On Timeout**: Notification for timed-out workflows
- **On Cancellation**: Optional cancellation notifications

## Monitoring and Observability

### Metrics Collected
- Workflow duration and success rates
- Job execution times and queue times
- Cache hit rates and storage usage
- Failure patterns and root causes

### Alerting Thresholds
- Workflow duration: > 60 minutes
- Job duration: > 30 minutes
- Queue time: > 10 minutes
- Failure rate: > 10%

### Dashboard Integration
- GitHub Actions built-in dashboard
- Custom monitoring dashboards
- Log aggregation and analysis

## Compliance and Governance

### Approval Requirements
- Security changes: 2 approvals required
- Infrastructure changes: 2 approvals required
- Breaking changes: 2 approvals required

### Audit Logging
- Enabled for all workflow executions
- 90-day retention period
- Comprehensive event tracking

### Change Management
- Ticket requirement for all changes
- Impact analysis documentation
- Rollback plan requirement
- Test plan validation

## Maintenance Procedures

### Regular Maintenance Tasks
1. **Weekly**: Cache cleanup and artifact rotation
2. **Monthly**: Dependency updates and security review
3. **Quarterly**: Configuration review and optimization
4. **Annually**: Comprehensive security audit

### Update Procedures
1. **Test Changes**: Test workflow changes in isolation
2. **Document Updates**: Update configuration documentation
3. **Communicate Changes**: Notify team of significant changes
4. **Monitor Impact**: Monitor performance after updates

### Troubleshooting Procedures
1. **Identify Issue**: Review workflow logs and artifacts
2. **Reproduce Locally**: Attempt local reproduction if possible
3. **Check Configuration**: Verify configuration files and permissions
4. **Escalate**: Escalate to maintainers if unresolved

## Getting Started

### Initial Setup
1. **Review Configuration**: Understand the existing configuration
2. **Test Workflows**: Run workflows manually to verify setup
3. **Configure Secrets**: Set up required repository secrets
4. **Enable Branch Protection**: Configure branch protection rules

### Adding New Workflows
1. **Use Template**: Start with `_template.yml`
2. **Customize**: Update triggers, jobs, and steps
3. **Test**: Test the workflow in isolation
4. **Document**: Update documentation for the new workflow

### Modifying Existing Workflows
1. **Backup**: Create backup of current configuration
2. **Test Changes**: Test changes in a feature branch
3. **Update Documentation**: Update relevant documentation
4. **Monitor**: Monitor workflow execution after changes

## Support and Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

### Tools
- **act**: Local GitHub Actions runner for testing
- **gh CLI**: GitHub CLI for workflow management
- **GitHub Actions VS Code Extension**: Visual workflow editing

### Community
- GitHub Discussions for questions and support
- GitHub Issues for bug reports and feature requests
- Regular team reviews and knowledge sharing sessions

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Initial release | Basic workflow configuration |
| 1.1.0 | [Date] | Added security scanning and performance monitoring |
| 1.2.0 | [Date] | Enhanced notification system and compliance features |

---

*This configuration is maintained as part of the Ona SDK project. For questions or support, contact the repository maintainers.*