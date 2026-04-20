#!/bin/bash
# AgentMind Release Automation Script
# This script automates the release process including version bumping,
# changelog generation, tagging, and publishing.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
}

# Check if working directory is clean
check_clean_working_dir() {
    if [[ -n $(git status --porcelain) ]]; then
        print_error "Working directory is not clean. Commit or stash changes first."
        git status --short
        exit 1
    fi
}

# Check if on main/master branch
check_main_branch() {
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        print_warning "Not on main/master branch (current: $current_branch)"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Get current version from setup.py
get_current_version() {
    python -c "import re; content = open('setup.py').read(); print(re.search(r'version=\"([^\"]+)\"', content).group(1))"
}

# Validate version format
validate_version() {
    local version=$1
    if [[ ! $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format: $version (expected: X.Y.Z)"
        exit 1
    fi
}

# Run tests
run_tests() {
    print_info "Running tests..."
    if command -v pytest &> /dev/null; then
        pytest tests/ -v || {
            print_error "Tests failed"
            exit 1
        }
        print_success "All tests passed"
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Run linting
run_linting() {
    print_info "Running linting..."
    if command -v ruff &> /dev/null; then
        ruff check src/ || print_warning "Linting issues found"
    else
        print_warning "ruff not found, skipping linting"
    fi
}

# Build package
build_package() {
    print_info "Building package..."
    rm -rf dist/ build/ *.egg-info
    python -m build || {
        print_error "Build failed"
        exit 1
    }
    print_success "Package built successfully"
}

# Generate changelog entry
generate_changelog() {
    local version=$1
    local date=$(date +%Y-%m-%d)

    print_info "Generating changelog for version $version..."

    # Get commits since last tag
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    local commits=""

    if [[ -n "$last_tag" ]]; then
        commits=$(git log $last_tag..HEAD --pretty=format:"- %s (%h)" --no-merges)
    else
        commits=$(git log --pretty=format:"- %s (%h)" --no-merges)
    fi

    # Create changelog entry
    local changelog_entry="## [$version] - $date\n\n### Changes\n\n$commits\n"

    # Prepend to CHANGELOG.md
    if [[ -f "CHANGELOG.md" ]]; then
        local temp_file=$(mktemp)
        echo -e "$changelog_entry" > "$temp_file"
        echo "" >> "$temp_file"
        cat CHANGELOG.md >> "$temp_file"
        mv "$temp_file" CHANGELOG.md
        print_success "Changelog updated"
    else
        print_warning "CHANGELOG.md not found, skipping changelog update"
    fi
}

# Create git tag
create_tag() {
    local version=$1
    local tag="v$version"

    print_info "Creating git tag: $tag"
    git tag -a "$tag" -m "Release version $version"
    print_success "Tag created: $tag"
}

# Push to remote
push_to_remote() {
    print_info "Pushing to remote..."
    git push origin --follow-tags || {
        print_error "Failed to push to remote"
        exit 1
    }
    print_success "Pushed to remote"
}

# Publish to PyPI
publish_to_pypi() {
    print_info "Publishing to PyPI..."

    if [[ ! -f "$HOME/.pypirc" ]]; then
        print_warning "~/.pypirc not found. Make sure you have PyPI credentials configured."
    fi

    read -p "Publish to PyPI? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python -m twine upload dist/* || {
            print_error "Failed to publish to PyPI"
            exit 1
        }
        print_success "Published to PyPI"
    else
        print_info "Skipping PyPI publication"
    fi
}

# Main release function
main() {
    print_header "AgentMind Release Automation"

    cd "$PROJECT_ROOT"

    # Pre-flight checks
    print_info "Running pre-flight checks..."
    check_git_repo
    check_clean_working_dir
    check_main_branch

    # Get version information
    local current_version=$(get_current_version)
    print_info "Current version: $current_version"

    # Determine release type
    echo ""
    echo "Select release type:"
    echo "  1) Patch (bug fixes)"
    echo "  2) Minor (new features, backwards compatible)"
    echo "  3) Major (breaking changes)"
    echo "  4) Custom version"
    echo ""
    read -p "Enter choice (1-4): " choice

    local new_version=""
    case $choice in
        1)
            new_version=$(python "$SCRIPT_DIR/bump_version.py" patch)
            ;;
        2)
            new_version=$(python "$SCRIPT_DIR/bump_version.py" minor)
            ;;
        3)
            new_version=$(python "$SCRIPT_DIR/bump_version.py" major)
            ;;
        4)
            read -p "Enter new version (X.Y.Z): " new_version
            validate_version "$new_version"
            python "$SCRIPT_DIR/bump_version.py" custom "$new_version"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    print_success "Version bumped: $current_version -> $new_version"

    # Run quality checks
    print_header "Quality Checks"
    run_tests
    run_linting

    # Build package
    print_header "Building Package"
    build_package

    # Generate changelog
    print_header "Generating Changelog"
    generate_changelog "$new_version"

    # Commit version changes
    print_info "Committing version changes..."
    git add setup.py CHANGELOG.md
    git commit -m "Release version $new_version"
    print_success "Changes committed"

    # Create tag
    print_header "Creating Release Tag"
    create_tag "$new_version"

    # Push to remote
    print_header "Pushing to Remote"
    push_to_remote

    # Publish to PyPI
    print_header "Publishing to PyPI"
    publish_to_pypi

    # Success message
    print_header "Release Complete!"
    print_success "Version $new_version released successfully"
    echo ""
    print_info "Next steps:"
    echo "  1. Create GitHub release: https://github.com/cym3118288-afk/AgentMind-Framework/releases/new"
    echo "  2. Update documentation if needed"
    echo "  3. Announce the release"
    echo ""
}

# Run main function
main "$@"
