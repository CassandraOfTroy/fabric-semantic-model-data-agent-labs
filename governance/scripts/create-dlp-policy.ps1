<#
.SYNOPSIS
Creates the Microsoft Purview DLP policy for the workshop governance demo.

.DESCRIPTION
The policy covers the workshop workspace only. When a Fabric item, such as a lakehouse, contains
international bank account numbers (IBAN), the item owner sees a policy tip on the item and an alert
appears in Microsoft Purview > Data loss prevention > Alerts.

Requirements:
- PowerShell 7 and the ExchangeOnlineManagement module (Install-Module ExchangeOnlineManagement -Scope CurrentUser)
- A Compliance Administrator (or higher) account
- The workspace must be on a Fabric or Premium capacity

Docs: https://learn.microsoft.com/purview/dlp-powerbi-get-started
      https://learn.microsoft.com/powershell/module/exchangepowershell/new-dlpcompliancepolicy
      https://learn.microsoft.com/powershell/module/exchangepowershell/new-dlpcompliancerule

.EXAMPLE
./create-dlp-policy.ps1 -WorkspaceId <workspace-guid> -UserPrincipalName admin@contoso.onmicrosoft.com
#>
param(
    [Parameter(Mandatory)] [string] $WorkspaceId,
    [Parameter(Mandatory)] [string] $UserPrincipalName,
    [string] $AlertRecipient = $UserPrincipalName,
    [string] $PolicyName = "Workshop - Fabric customer bank data",
    [string] $RuleName = "IBAN in Fabric items",
    [ValidateSet("Enable", "TestWithNotifications", "TestWithoutNotifications")] [string] $Mode = "Enable"
)

$ErrorActionPreference = "Stop"
Import-Module ExchangeOnlineManagement
Connect-IPPSSession -UserPrincipalName $UserPrincipalName -ShowBanner:$false

if (-not (Get-DlpCompliancePolicy -Identity $PolicyName -ErrorAction SilentlyContinue)) {
    New-DlpCompliancePolicy -Name $PolicyName -Mode $Mode -PowerBIDlpLocation $WorkspaceId `
        -Comment "Fabric hands-on workshop: detects customer bank account numbers (IBAN) in Fabric items of the workshop workspace." | Out-Null
    Write-Host "Created policy '$PolicyName' ($Mode)"
} else {
    Write-Host "Policy '$PolicyName' already exists"
}

if (-not (Get-DlpComplianceRule -Identity $RuleName -ErrorAction SilentlyContinue)) {
    # -GenerateAlert expects email addresses of the alert recipients.
    New-DlpComplianceRule -Name $RuleName -Policy $PolicyName `
        -ContentContainsSensitiveInformation @{ Name = "International Banking Account Number (IBAN)"; minCount = "1" } `
        -NotifyUser "Owner" `
        -NotifyPolicyTipCustomText "This item contains customer bank account numbers (IBAN). Move the data to a restricted workspace or remove the column." `
        -GenerateAlert $AlertRecipient -ReportSeverityLevel "High" | Out-Null
    Write-Host "Created rule '$RuleName'"
} else {
    Write-Host "Rule '$RuleName' already exists"
}

Get-DlpCompliancePolicy -Identity $PolicyName | Select-Object Name, Mode, DistributionStatus, PowerBIDlpLocation | Format-List
Get-DlpComplianceRule -Policy $PolicyName | Select-Object Name, NotifyUser, GenerateAlert, ReportSeverityLevel | Format-List
Disconnect-ExchangeOnline -Confirm:$false
