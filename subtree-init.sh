#!/bin/bash

ansibleRemoteName="ansible_callback_plugin_api_post"
ansibleGitRepositoryUrl="git@github.com:massimilianovallascas/ansible_callback_plugin_api_post.git"
# ansibleGitRepositoryUrl="https://github.com/massimilianovallascas/ansible_callback_plugin_api_post.git"
ansibleSubtreeFolder="ansible_callback_plugin_api_post"

bashScript="subtree-init.sh"
callbackPluginsFolder="callback_plugins"
callbackPluginName="api.py"
currentFolder=$(pwd)
currentScript="${0}"

bashScriptPath=${currentFolder}/${currentScript}
bashScriptSubtreePath=${currentFolder}/${ansibleSubtreeFolder}/${bashScript}
callbackPluginPath=${currentFolder}/${callbackPluginsFolder}/${callbackPluginName}
callbackPluginSubtreePath=${currentFolder}/${ansibleSubtreeFolder}/${callbackPluginsFolder}/${callbackPluginName}

if [[ ! -z $(git status -s) ]]; then
    echo "Your repository has uncommitted changes, please commit your changes before running this script"
    exit 1
fi

echo "Add the subtree as a remote"
git remote add ${ansibleRemoteName} ${ansibleGitRepositoryUrl}
echo "Add the subtree but now we can refer to the remote in short form"
git subtree add --prefix ${ansibleSubtreeFolder} ${ansibleRemoteName} master --squash
echo "Fetch from remote"
git fetch ${ansibleRemoteName} master
echo "Pull from remote"
git subtree pull --prefix ${ansibleSubtreeFolder} ${ansibleRemoteName} master --squash

function copyPlugin {
    echo "Copying the subtree version of the plugin into your ${callbackPluginsFolder} folder"
    mkdir -p ${currentFolder}/${callbackPluginsFolder}
    cp ${callbackPluginSubtreePath} ${callbackPluginPath}
}

function copyBashScript {
    echo "Copying the subtree version of the bash script to ${bashScriptSubtreePath}"
    cp ${bashScriptSubtreePath} ${bashScriptPath}
}

if [[ -f "${callbackPluginSubtreePath}" && -f "${callbackPluginPath}" ]]; then
    if ! cmp -s "${callbackPluginSubtreePath}" "${callbackPluginPath}"; then
        echo "Your API Callback Plugin is different from the one in the repository"
        read -p 'Do you want to update it? [Y/n] : ' updatePlugin
        if [[ "${updatePlugin}" == "y" ]] || [[ ${updatePlugin} == "Y" ]]; then
            copyPlugin
        else
            echo "Current plugin won't be updated"
        fi
    else
        echo "Your API Callback Plugin is not different from the one in the repository"
    fi
else
    copyPlugin
fi

if ! cmp -s "${bashScriptSubtreePath}" "${bashScriptPath}"; then
    echo "Your bash script is different from the one in the repository"
    read -p 'Do you want to update it? [Y/n] : ' updateScript
    if [[ "${updateScript}" == "y" ]] || [[ ${updateScript} == "Y" ]]; then
        copyBashScript
    else
        echo "Current bash script won't be updated"
    fi
else
    echo "Your bash script is not different from the one in the repository"
fi

read -p 'Do you want to delete the subtree folder from the project? (reference in the git config will not be deleted) [Y/n] : ' delete
if [[ "${delete}" == "y" ]] || [[ ${delete} == "Y" ]]; then
    rm -rf ${currentFolder}/${ansibleSubtreeFolder}
fi