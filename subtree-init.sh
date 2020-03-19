#!/bin/bash

ansibleRemoteName="ansible_callback_plugin_api_post"
ansibleGitRepositoryUrl="git@github.com:massimilianovallascas/ansible_callback_plugin_api_post.git"
ansibleSubtreeFolder="ansible_callback_plugin_api_post"

currentFolder=$(pwd)
callbackPluginsFolder="callback_plugins"
callbackPluginName="api.py"

callbackPluginSubtreePath=${currentFolder}/${ansibleSubtreeFolder}/${callbackPluginsFolder}/${callbackPluginName}
callbackPluginPath=${currentFolder}/${callbackPluginsFolder}/${callbackPluginName}

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

if [[ -f "${callbackPluginSubtreePath}" && -f "${callbackPluginPath}" ]]; then
    if ! cmp -s "${callbackPluginSubtreePath}" "${callbackPluginPath}"; then
        echo "Your API Callback Plugin is different from the one in the repository"
        read -p 'Do you want to update it? [Y/n] : ' update
        if [[ "${update}" == "y" ]] || [[ ${update} == "Y" ]]; then
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

read -p 'Do you want to delete the subtree folder from the project? (reference in the git config will not be deleted) [Y/n] : ' delete
if [[ "${delete}" == "y" ]] || [[ ${delete} == "Y" ]]; then
    rm -rf ${currentFolder}/${ansibleSubtreeFolder}
fi