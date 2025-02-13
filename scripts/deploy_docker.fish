#! /usr/bin/env fish

# Initialize flags
set YES_FLAG false
set NO_FLAG false

# Parse arguments
for arg in $argv
    switch $arg
        case '--yes'
            set YES_FLAG true
        case '--no'
            set NO_FLAG true
    end
end

# Prompt the user if neither --yes nor --no is provided
if not $YES_FLAG and not $NO_FLAG
    read -P "Do you want to reset hard to origin/main? (y/n): " response
    if string match -r '^[Yy]$' $response
        set YES_FLAG true
    else
        set NO_FLAG true
    end
end

# Perform the reset if confirmed
if $YES_FLAG
    git fetch && git reset --hard origin/main
end

docker compose up --build
