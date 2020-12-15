function Remove-Chocolatey{
    <#
        .SYNOPSIS
            This function removes chocolatey binaries and local configs such as env var.
            Also removes local copy of packages.config file that was used to bootstrap machine    
    #>
    Write-Output "+++ Deleting Chocolatey package config file +++"
    Remove-Item -Path C:\packages.config

    if (!$env:ChocolateyInstall) {
        Write-Warning "The ChocolateyInstall environment variable was not found. `n Chocolatey is not detected as installed. Nothing to do"
        return
        }
    if (!(Test-Path "$env:ChocolateyInstall")) {
    Write-Warning "Chocolatey installation not detected at '$env:ChocolateyInstall'. `n Nothing to do."
    return
    }

    $userPath = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment').GetValue('PATH', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames).ToString()
    $machinePath = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey('SYSTEM\CurrentControlSet\Control\Session Manager\Environment\').GetValue('PATH', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames).ToString()
    
    Write-Output "User PATH: " + $userPath | Out-File "C:\PATH_backups_ChocolateyUninstall.txt" -Encoding UTF8 -Force
    Write-Output "Machine PATH: " + $machinePath | Out-File "C:\PATH_backups_ChocolateyUninstall.txt" -Encoding UTF8 -Force
    
    if ($userPath -like "*$env:ChocolateyInstall*") {
    Write-Output "Chocolatey Install location found in User Path. Removing..."
    # WARNING: This could cause issues after reboot where nothing is
    # found if something goes wrong. In that case, look at the backed up
    # files for PATH.
    [System.Text.RegularExpressions.Regex]::Replace($userPath, [System.Text.RegularExpressions.Regex]::Escape("$env:ChocolateyInstall\bin") + '(?>;)?', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) | %{[System.Environment]::SetEnvironmentVariable('PATH', $_.Replace(";;",";"), 'User')}
    }
    
    if ($machinePath -like "*$env:ChocolateyInstall*") {
    Write-Output "Chocolatey Install location found in Machine Path. Removing..."
    # WARNING: This could cause issues after reboot where nothing is
    # found if something goes wrong. In that case, look at the backed up
    # files for PATH.
    [System.Text.RegularExpressions.Regex]::Replace($machinePath, [System.Text.RegularExpressions.Regex]::Escape("$env:ChocolateyInstall\bin") + '(?>;)?', '', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase) | %{[System.Environment]::SetEnvironmentVariable('PATH', $_.Replace(";;",";"), 'Machine')}
    }
    
    # Adapt for any services running in subfolders of ChocolateyInstall
    $agentService = Get-Service -Name chocolatey-agent -ErrorAction SilentlyContinue
    if ($agentService -and $agentService.Status -eq 'Running') { $agentService.Stop() }
    # TODO: add other services here
    
    # delete the contents (remove -WhatIf to actually remove)
    Remove-Item -Recurse -Force "$env:ChocolateyInstall" -WhatIf
    
    [System.Environment]::SetEnvironmentVariable("ChocolateyInstall", $null, 'User')
    [System.Environment]::SetEnvironmentVariable("ChocolateyInstall", $null, 'Machine')
    [System.Environment]::SetEnvironmentVariable("ChocolateyLastPathUpdate", $null, 'User')
    [System.Environment]::SetEnvironmentVariable("ChocolateyLastPathUpdate", $null, 'Machine')
}

function Remove-PackerUser{
    <#
        .SYNOPSIS
            This removes the local packer_user account used for packer winRM connection
    #>
    param(
        [String] $userAccount # default, packer_user
    )
    Write-Output "+++ Removing local user account for packer +++"
    Remove-LocalUser -Name $userAccount
}

function Remove-WinRMConfig {
    <#
        .SYNOPSIS
            This undos the winrm config set up for packer. Removes local cert, listener, firewall rules and disables windows service from starting
    #>

    Write-Output "+++ Removing Packer WinRM and required configs +++"
    # Remove HTTP listener and deleting the self-signed cert for packer winrm connection
    Remove-Item -Path WSMan:\Localhost\listener\listener* -Recurse
    # Deleting selfsigned cert used for HTTPS connection
    $certName = "packer"
    Get-ChildItem -Path Cert:\LocalMachine\My | Where-Object {  $_.FriendlyName -like $certName  } | Remove-Item
    # Closing WinRM HTTPS firewall
    $firewallRuleName = "WinRM"
    Remove-NetFirewallRule -DisplayName $firewallRuleName
    Write-Output "+++ Disabling WinRM +++"
    Disable-PSRemoting
    # Disabling local winrm service from auto starting 
    Stop-Service -Name winrm
    Set-Service -Name winrm -StartupType Manual
}

# Kick off clean up script

Remove-Chocolatey
Remove-PackerUser -userAccount "packer_user"
Remove-WinRMConfig
# Finally, delete the cleanup script itself
Remove-Item -Path $MyInvocation.MyCommand.Source -Force
