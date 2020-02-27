# Remote API POST Ansible Callback Plugin
An Ansible Callback Plugin to send information about Ansible Play to a remote API.


## Use the callback in your Ansible repository
In order to use the callback plugin in your playbook:
- Create a folder in the root of the repository called `callback_plugins`
- Copy the `api.py` file inside the folder you just created

Ansible should load the callback plugin on runtime without any change to your onfiguration or your playbook. There are two ways to send the required variables to the callback plugin:
- Add a `callback_api` section to your ansible.cfg file with all the variables
- Use environment variables (remember to export them)  


## Ansible tower integration
In order to use the callback plugin with AWX you need to follow the steps below:
- Set a new Ansible tower credential type:  
  - Login in Ansible tower
  - Click on the `Credential Types` option on the main menu (left side under `ADMINISTRATION` section)
  - Click on the Plus `+` button on the top right corner of the main page
  - Add a name for the new credential type you are creating
  - Copy the content of the `awx_config/transaction_api_credentials-configuration.yml` file in the `INPUT CONFIGURATION` section
  - Copy the content of the `awx_config/transaction_api_credentials-injector.yml` file in the `INJECTOR CONFIGURATION` section
  - Click on the `SAVE` button

- Create a new set of credentials
  - Login in Ansible tower
  - Click on the `Credentials` option on the main menu (left side under `RESOURCES` section)
  - Click on the Plus `+` button on the top right corner of the main page
  - Add a name for the new credential set you are creating then select the `CREDENTIAL TYPE` from the dropdown (the name of the type is the one you set on the section above)
  - Click on the `SAVE` button

- Add credentials to a template
  - Login in Ansible tower
  - Click on the `Templates` option on the main menu (left side under `RESOURCES` section)
  - Select one of your existing template or create a new one clicking on the Plus `+` button on the top right corner of the main page
  - In order to use the `credentials` created on the section above
    - Click on the spotlight on the left side of the `CREDENTIALS` field
    - In the pop-up select the `CREDENTIAL TYPE` in the drop-down, the name is the same you set on the first section
    - Click on `SELECT`
    - On the main template window you should be able to see the credential you selected inside the `CREDENTIALS` input 
    - Click on the `SAVE` button


---
### Environment variables
**CALLBACK_API_ENDPOINT**: API endpoint (required)  
**CALLBACK_API_USERNAME**: Username to access the API endpoint (required)  
**CALLBACK_API_PASSWORD**: Password to access the API endpoint (required)  
**CALLBACK_API_REQUIRED_VARIABLES**: Extra variables to be present so that the POST action will be submitted, if empty default values will be loaded (resource_id,transaction_id)  
**CALLBACK_API_SKIP_EMPTY_TASK_NAME**: If the task doesn't have a name set then the POST action will be skipped   
**CALLBACK_API_VERBOSE**: Send verbose POST to API endpoint  
