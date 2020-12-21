Write-Output "+++ Running Chocolatey… +++"

# clean exit or reboot pending: https://chocolatey.org/docs/commandsinstall#exit-codes
$validExitCodes = 0, 3010

# Globally Auto confirm every action
$commandAutoConfirm = 'choco feature enable -n allowGlobalConfirmation'
$commandInstall = 'choco install C:\packages.config -y --no-progress'

try
{
    Invoke-Expression -Command $commandAutoConfirm
    Invoke-Expression -Command $commandInstall
    
    if ($LASTEXITCODE -notin $validExitCodes)
    {
        throw "Error encountered during package installation with status: $($LASTEXITCODE)"
    }
    else
    {
        Write-Output ""
        Write-Output "Chocolatey packages has been installed successfully!"
    }
}
catch
{
    throw "Error encountered during chocolatey operation: $($Error[0].Exception)"
}


