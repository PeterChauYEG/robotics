export BASH_CONF="bash_profile"

# useful aliases
alias bs="source ~/.bash_profile"
alias profile="cat .bash_profile"

alias gc="git commit -m"
alias gs="git status"
alias ga="git add --a"
alias gp="git push origin "
alias gm="git checkout main"
alias gum="git pull origin main"
alias gu="git pull origin "
alias gcob="git checkout -b "
alias gcc="git checkout "

alias la="ls -la"
alias ".."="cd .."
alias "..."="cd ..; cd .."

alias drone ="python3 src/drone.py ws://192.168.0.182:8000"
alias i2c_test="python3 src/i2c_test.py"
