#!/bin/bash
tmuxSnapshot=/.tmux_snapshot
tmuxEXE=/usr/local/bin/tmux
save_snap()
{
        ${tmuxEXE} list-windows -a -F"#{session_name} #{window_name} #{pane_current_command} #{pane_current_path}" > ${tmuxSnapshot}
}

restore_snap()
{
        ${tmuxEXE} start-server
        while IFS=' ' read -r session_name window_name pane_current_command pane_current_path
        do
                ${tmuxEXE} has-session -t "${session_name}" 2>/dev/null
                if [ $? != 0 ]
                then
                        ${tmuxEXE} new-session -d -s "${session_name}" -n ${window_name}
                else
                        ${tmuxEXE} new-window -d -t ${session_name} -n "${window_name}"
                fi
                ${tmuxEXE} send-keys -t "${session_name}:${window_name}" "cd ${pane_current_path}; echo \"Hint: last time you are executing '${pane_current_command}'.\"" ENTER
        done < ${tmuxSnapshot}
}

ps aux|grep -w tmux|grep -v grep
if [ $? != 0 ]
then
        restore_snap
else
        save_snap
fi

