# BGXAI_ONE_FILE_SELECTOR_019_GUARD
# Experimental BGXUN1 v018 temporarily PAUSED after real 105/355 oscillation.
# No game files changed by choices 1 and 3. Original BGXAI_UPDATE.cmd unchanged.
Write-Host ''
Write-Host ' BGXAI UPDATE - SAFE STOCK BASELINE REBUILD'
Write-Host ' 1 = BGXUN1 experimental installer [PAUSED: known combat regression]'
Write-Host ' 2 = Update legacy BGXAI 0.6.x role scripts (original behavior)'
Write-Host ' 3 = Exit without changes [default]'
Write-Host ''
$bgxChoice=Read-Host 'Choose [3]'
if([string]::IsNullOrWhiteSpace($bgxChoice)) {$bgxChoice='3'}
if($bgxChoice -eq '3'){Write-Host 'No files changed.';exit 0}
if($bgxChoice -eq '1'){
    Write-Host 'PAUSED: BGXUN1 0.1.8 failed real ranged retreat/reengage tests.'
    Write-Host 'Use the existing working Advanced AI in the character script menu.'
    Write-Host 'No files have been modified.'
    exit 0
}
if($bgxChoice -ne '2'){Write-Host 'Invalid choice; nothing changed.';exit 1}
# Choice 2 falls through unchanged to the historic BGXAI 0.6.x try/catch below.