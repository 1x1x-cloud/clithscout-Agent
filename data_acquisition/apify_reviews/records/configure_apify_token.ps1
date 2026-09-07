Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
$taskStatusPath = Join-Path $PSScriptRoot 'token_input_status.json'
function Write-TaskStatus([string]$value) {
    [ordered]@{status=$value;timestamp_utc=[DateTime]::UtcNow.ToString('o');secret_logged=$false} |
        ConvertTo-Json | Set-Content -LiteralPath $taskStatusPath -Encoding UTF8
}
$taskWorkspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskPython = Join-Path $taskWorkspace '.venv-1688-pilot/Scripts/python.exe'
$taskReceiver = Join-Path $PSScriptRoot 'store_apify_token.py'
$taskForm = New-Object System.Windows.Forms.Form
$taskForm.Text = 'Apify API token - local secure entry'
$taskForm.ClientSize = New-Object System.Drawing.Size(560,210)
$taskForm.StartPosition = 'CenterScreen'
$taskForm.FormBorderStyle = 'FixedDialog'
$taskForm.MaximizeBox = $false
$taskForm.MinimizeBox = $false
$taskForm.TopMost = $true
$taskInfo = New-Object System.Windows.Forms.Label
$taskInfo.Location = New-Object System.Drawing.Point(20,18)
$taskInfo.Size = New-Object System.Drawing.Size(520,48)
$taskInfo.Text = 'Paste your Apify API token below. Ctrl+V is supported.' + [Environment]::NewLine + 'Saved only in Windows Credential Manager. No run will start.'
$taskBox = New-Object System.Windows.Forms.TextBox
$taskBox.Location = New-Object System.Drawing.Point(20,78)
$taskBox.Size = New-Object System.Drawing.Size(520,28)
$taskBox.UseSystemPasswordChar = $true
$taskBox.ShortcutsEnabled = $true
$taskBox.MaxLength = 4096
$taskSave = New-Object System.Windows.Forms.Button
$taskSave.Text = 'Save token'
$taskSave.Location = New-Object System.Drawing.Point(318,135)
$taskSave.Size = New-Object System.Drawing.Size(110,32)
$taskCancel = New-Object System.Windows.Forms.Button
$taskCancel.Text = 'Cancel'
$taskCancel.Location = New-Object System.Drawing.Point(438,135)
$taskCancel.Size = New-Object System.Drawing.Size(102,32)
$taskForm.Controls.AddRange(@($taskInfo,$taskBox,$taskSave,$taskCancel))
$taskForm.AcceptButton = $taskSave
$taskForm.CancelButton = $taskCancel
$script:taskSaved = $false
$taskSave.Add_Click({
    $taskValue = $taskBox.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($taskValue) -or $taskValue -match '[\s\x00-\x1F\x7F-\xFF]') {
        [void][System.Windows.Forms.MessageBox]::Show('Please paste the token text without spaces or control characters.','Check token')
        return
    }
    $taskProcess = $null
    try {
        $taskStart = New-Object System.Diagnostics.ProcessStartInfo
        $taskStart.FileName = $taskPython
        $taskStart.Arguments = '-B "' + $taskReceiver + '"'
        $taskStart.UseShellExecute = $false
        $taskStart.CreateNoWindow = $true
        $taskStart.RedirectStandardInput = $true
        $taskStart.RedirectStandardOutput = $true
        $taskStart.RedirectStandardError = $true
        $taskProcess = New-Object System.Diagnostics.Process
        $taskProcess.StartInfo = $taskStart
        [void]$taskProcess.Start()
        $taskProcess.StandardInput.Write($taskValue)
        $taskProcess.StandardInput.Close()
        $taskValue = $null
        $taskOutput = $taskProcess.StandardOutput.ReadToEnd()
        $null = $taskProcess.StandardError.ReadToEnd()
        $taskProcess.WaitForExit()
        if ($taskProcess.ExitCode -ne 0 -or $taskOutput.Trim() -ne 'SAVED') {
            [void][System.Windows.Forms.MessageBox]::Show('Could not save. Paste only the API token and try again.','Not saved')
            Write-TaskStatus 'save_failed'
            return
        }
        $script:taskSaved = $true
        Write-TaskStatus 'saved'
        $taskBox.Clear()
        $taskForm.Close()
    } catch {
        Write-TaskStatus 'save_failed'
        [void][System.Windows.Forms.MessageBox]::Show('Could not save to Windows Credential Manager.','Not saved')
    } finally {
        $taskValue = $null
        if ($taskProcess) { $taskProcess.Dispose() }
    }
})
$taskCancel.Add_Click({ $taskForm.Close() })
$taskForm.Add_Shown({ Write-TaskStatus 'awaiting_input'; $taskBox.Focus() })
$taskForm.Add_FormClosed({
    $taskBox.Clear()
    if (-not $script:taskSaved) { Write-TaskStatus 'cancelled' }
})
Write-TaskStatus 'starting'
[void]$taskForm.ShowDialog()
$taskForm.Dispose()

