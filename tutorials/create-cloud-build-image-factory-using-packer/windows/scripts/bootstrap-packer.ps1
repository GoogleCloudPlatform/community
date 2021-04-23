# https://docs.microsoft.com/en-us/windows/win32/winrm/winrm-powershell-commandlets

Write-Output "+++ Running Bootstrap Script for setting up packer +++"

Set-ExecutionPolicy Unrestricted -Scope LocalMachine -Force -ErrorAction Ignore

# Don't set this before Set-ExecutionPolicy as it throws an error
$ErrorActionPreference = "stop"

# Remove HTTP listener and creating a new self-signed cert for packer winrm connection
Remove-Item -Path WSMan:\Localhost\listener\listener* -Recurse

# Creating new selfsigned cert for HTTPS connection
$certName = "packer"
$Cert = New-SelfSignedCertificate -CertstoreLocation Cert:\LocalMachine\My -DnsName $certName -FriendlyName $certName
New-Item -Path WSMan:\LocalHost\Listener -Transport HTTPS -Address * -CertificateThumbPrint $Cert.Thumbprint -Force

# WinRM stuff
Write-Output "+++ Setting up WinRM+++ "

#cmd.exe /c winrm quickconfig -q
$firewallRuleName = "WinRM"
cmd.exe /c winrm set "winrm/config" '@{MaxTimeoutms="1800000"}'
cmd.exe /c winrm set "winrm/config/winrs" '@{MaxMemoryPerShellMB="1024"}'
cmd.exe /c winrm set "winrm/config/service" '@{AllowUnencrypted="true"}'
cmd.exe /c winrm set "winrm/config/client" '@{AllowUnencrypted="true"}'
cmd.exe /c winrm set "winrm/config/service/auth" '@{Basic="true"}'
cmd.exe /c winrm set "winrm/config/client/auth" '@{Basic="true"}'
cmd.exe /c winrm set "winrm/config/service/auth" '@{CredSSP="true"}'
cmd.exe /c winrm set "winrm/config/listener?Address=*+Transport=HTTPS" "@{Port=`"5986`";Hostname=`"packer`";CertificateThumbprint=`"$($Cert.Thumbprint)`"}"
cmd.exe /c netsh advfirewall firewall set rule group="remote administration" new enable=yes
cmd.exe /c netsh advfirewall firewall add rule name=$firewallRuleName dir=in protocol=tcp localport=5986 action=allow
Stop-Service -Name winrm
Set-Service -Name winrm -StartupType Auto
Start-Service -Name winrm