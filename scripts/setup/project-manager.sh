#!/bin/zsh

# GitHub Project Management Helper Script
# Quick commands for managing GitHub Projects via CLI

PROJECT_ID="2"
PROJECT_OWNER="fowler013"
PROJECT_BOARD_ID="PVT_kwHOAlQYis4A-YHu"
STATUS_FIELD_ID="PVTSSF_lAHOAlQYis4A-YHuzgxzFXU"
PRIORITY_FIELD_ID="PVTSSF_lAHOAlQYis4A-YHuzgxzFlk"
SIZE_FIELD_ID="PVTSSF_lAHOAlQYis4A-YHuzgxzFlo"

# Status option IDs
STATUS_BACKLOG="f75ad846"
STATUS_READY="61e4505c"
STATUS_IN_PROGRESS="47fc9ee4"
STATUS_IN_REVIEW="df73e18b"
STATUS_DONE="98236657"

# Priority option IDs
PRIORITY_P0="79628723"
PRIORITY_P1="0a877460"
PRIORITY_P2="da944a9c"

# Size option IDs
SIZE_XS="6c6483d2"
SIZE_S="f784b110"
SIZE_M="7515a9f1"
SIZE_L="817d0097"
SIZE_XL="db339eb2"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display project overview
project_overview() {
    echo "${BLUE}📊 CampPowerUp Kanban Board Overview${NC}"
    echo "========================================"
    gh project item-list $PROJECT_ID --owner $PROJECT_OWNER --format json | \
        jq -r '.items[] | "PR #\(.content.number): \(.content.title)\n  Status: \(.status) | Priority: \(.priority // "None") | Size: \(.size // "None")\n"'
}

# Function to add PR to project
add_pr_to_project() {
    local pr_number=$1
    if [ -z "$pr_number" ]; then
        echo "${YELLOW}Usage: add_pr_to_project <PR_NUMBER>${NC}"
        return 1
    fi
    
    echo "${GREEN}Adding PR #$pr_number to project...${NC}"
    gh project item-add $PROJECT_ID --owner $PROJECT_OWNER --url "https://github.com/${PROJECT_OWNER}/CampPowerUp/pull/${pr_number}"
}

# Function to set PR status
set_pr_status() {
    local pr_number=$1
    local status=$2
    
    if [ -z "$pr_number" ] || [ -z "$status" ]; then
        echo "${YELLOW}Usage: set_pr_status <PR_NUMBER> <STATUS>${NC}"
        echo "Status options: backlog, ready, in-progress, in-review, done"
        return 1
    fi
    
    # Get status ID
    case $status in
        backlog) status_id=$STATUS_BACKLOG ;;
        ready) status_id=$STATUS_READY ;;
        in-progress) status_id=$STATUS_IN_PROGRESS ;;
        in-review) status_id=$STATUS_IN_REVIEW ;;
        done) status_id=$STATUS_DONE ;;
        *) echo "${YELLOW}Invalid status: $status${NC}"; return 1 ;;
    esac
    
    # Get item ID
    item_id=$(gh project item-list $PROJECT_ID --owner $PROJECT_OWNER --format json | \
        jq -r ".items[] | select(.content.number == $pr_number) | .id")
    
    if [ -z "$item_id" ]; then
        echo "${YELLOW}PR #$pr_number not found in project${NC}"
        return 1
    fi
    
    echo "${GREEN}Setting PR #$pr_number to status: $status${NC}"
    gh project item-edit --project-id $PROJECT_BOARD_ID --id "$item_id" \
        --field-id $STATUS_FIELD_ID --single-select-option-id $status_id
}

# Function to set PR priority
set_pr_priority() {
    local pr_number=$1
    local priority=$2
    
    if [ -z "$pr_number" ] || [ -z "$priority" ]; then
        echo "${YELLOW}Usage: set_pr_priority <PR_NUMBER> <PRIORITY>${NC}"
        echo "Priority options: p0, p1, p2"
        return 1
    fi
    
    # Get priority ID
    case $priority in
        p0) priority_id=$PRIORITY_P0 ;;
        p1) priority_id=$PRIORITY_P1 ;;
        p2) priority_id=$PRIORITY_P2 ;;
        *) echo "${YELLOW}Invalid priority: $priority${NC}"; return 1 ;;
    esac
    
    # Get item ID
    item_id=$(gh project item-list $PROJECT_ID --owner $PROJECT_OWNER --format json | \
        jq -r ".items[] | select(.content.number == $pr_number) | .id")
    
    if [ -z "$item_id" ]; then
        echo "${YELLOW}PR #$pr_number not found in project${NC}"
        return 1
    fi
    
    echo "${GREEN}Setting PR #$pr_number to priority: $priority${NC}"
    gh project item-edit --project-id $PROJECT_BOARD_ID --id "$item_id" \
        --field-id $PRIORITY_FIELD_ID --single-select-option-id $priority_id
}

# Function to set PR size
set_pr_size() {
    local pr_number=$1
    local size=$2
    
    if [ -z "$pr_number" ] || [ -z "$size" ]; then
        echo "${YELLOW}Usage: set_pr_size <PR_NUMBER> <SIZE>${NC}"
        echo "Size options: xs, s, m, l, xl"
        return 1
    fi
    
    # Get size ID
    case $size in
        xs) size_id=$SIZE_XS ;;
        s) size_id=$SIZE_S ;;
        m) size_id=$SIZE_M ;;
        l) size_id=$SIZE_L ;;
        xl) size_id=$SIZE_XL ;;
        *) echo "${YELLOW}Invalid size: $size${NC}"; return 1 ;;
    esac
    
    # Get item ID
    item_id=$(gh project item-list $PROJECT_ID --owner $PROJECT_OWNER --format json | \
        jq -r ".items[] | select(.content.number == $pr_number) | .id")
    
    if [ -z "$item_id" ]; then
        echo "${YELLOW}PR #$pr_number not found in project${NC}"
        return 1
    fi
    
    echo "${GREEN}Setting PR #$pr_number to size: $size${NC}"
    gh project item-edit --project-id $PROJECT_BOARD_ID --id "$item_id" \
        --field-id $SIZE_FIELD_ID --single-select-option-id $size_id
}

# Main menu
show_menu() {
    echo ""
    echo "${BLUE}🎯 GitHub Project Manager${NC}"
    echo "=========================="
    echo "1) View project overview"
    echo "2) Add PR to project"
    echo "3) Set PR status"
    echo "4) Set PR priority"
    echo "5) Set PR size"
    echo "0) Exit"
    echo ""
}

# Main script
if [ "$1" = "overview" ]; then
    project_overview
elif [ "$1" = "add" ]; then
    add_pr_to_project $2
elif [ "$1" = "status" ]; then
    set_pr_status $2 $3
elif [ "$1" = "priority" ]; then
    set_pr_priority $2 $3
elif [ "$1" = "size" ]; then
    set_pr_size $2 $3
else
    # Interactive mode
    while true; do
        show_menu
        read "choice?Enter choice: "
        
        case $choice in
            1) project_overview ;;
            2) 
                read "pr?Enter PR number: "
                add_pr_to_project $pr
                ;;
            3)
                read "pr?Enter PR number: "
                read "status?Enter status (backlog/ready/in-progress/in-review/done): "
                set_pr_status $pr $status
                ;;
            4)
                read "pr?Enter PR number: "
                read "priority?Enter priority (p0/p1/p2): "
                set_pr_priority $pr $priority
                ;;
            5)
                read "pr?Enter PR number: "
                read "size?Enter size (xs/s/m/l/xl): "
                set_pr_size $pr $size
                ;;
            0) echo "Goodbye!"; exit 0 ;;
            *) echo "${YELLOW}Invalid choice${NC}" ;;
        esac
    done
fi
