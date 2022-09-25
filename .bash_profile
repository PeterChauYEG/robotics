export BASH_CONF="bash_profile"

# useful aliases
alias bs="source ~/robotics/.bash_profile"
alias profile="cat .bash_profile"
alias updateb="cp ~/robotics/.bash_profile ~/.bash_profile"

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

alias drone="python3 ~/robotics/src/drone.py ws://192.168.0.182:8000"
alias i2c_test="python3 ~/robotics/src/i2c_test.py"
alias oled_test="python3 ~/robotics/src/oled_test.py"
alias motor_test="python3 ~/robotics/src/motor_test.py"
