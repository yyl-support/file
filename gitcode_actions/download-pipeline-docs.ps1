$ErrorActionPreference = 'Stop'

$destination = Join-Path $PSScriptRoot 'gitcode-pipeline-docs'
$urls = @(
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/action-yml-metadata-syntax',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/plugin-development-guide',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/plugin-packaging',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/plugin-project-structure',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/plugin-security-specification',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/runtime-environment-variables',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/action-development/top-level-fields',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/artifacts-and-cache',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/runner-and-environment',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/trigger-events',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/variables-secrets-context-expressions',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/core-concepts/workflow-job-step-action',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/go-ci',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/java-gradle-ci',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/java-maven-ci',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/nodejs-ci',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/pr-code-check-example',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/examples/python-ci',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/overview',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/pipeline-intro1',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/quick-start',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/runner-management/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/runner-management/configuring-images-toolchains',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/runner-management/selecting-runner-labels',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/runner-management/using-hosted-runners',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/runner-management/using-self-hosted-runners',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/running-pipelines/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/running-pipelines/manually-trigger-pipeline',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/running-pipelines/rerun-failed-jobs',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/running-pipelines/view-job-logs',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/running-pipelines/view-run-results',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/security-permissions/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/security-permissions/pr-mr-pipeline-security',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/security-permissions/token-permissions',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/security-permissions/using-secrets',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/context',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/expressions',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/runner-images-tools',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/trigger-events',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/variables',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/syntax-reference/workflow-commands',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-conditional-execution',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-dependencies-order',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-jobs',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-matrix-builds',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-steps',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/configure-triggers',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/pass-output-between-jobs',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/upload-download-artifacts',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/using-actions',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/using-dependency-cache',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/using-script-commands',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/using-variables-secrets',
    'https://docs.gitcode.com/docs/help/home/org_project/pipeline/writing-pipelines/workflow-file-location-structure'
)

New-Item -ItemType Directory -Force -Path $destination | Out-Null
$assets = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$savedPages = @()

foreach ($url in $urls) {
    $uri = [Uri]$url
    $relative = $uri.AbsolutePath.Trim('/')
    $relative = if ([string]::IsNullOrWhiteSpace($relative)) { 'index' } else { $relative }
    $output = Join-Path $destination ($relative + '.html')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $output) | Out-Null
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    [System.IO.File]::WriteAllText($output, $response.Content, [System.Text.UTF8Encoding]::new($false))
    $savedPages += [PSCustomObject]@{ Url = $url; File = ($output.Substring($destination.Length + 1) -replace '\\', '/') }

    [regex]::Matches($response.Content, '(?i)(?:src|href)=["'']([^"''#?]+)') | ForEach-Object {
        $value = $_.Groups[1].Value
        if ($value -match '^(?:/|https://docs\.gitcode\.com/)') {
            try {
                $assetUri = [Uri]::new($uri, $value)
                if ($assetUri.Host -eq 'docs.gitcode.com' -and $assetUri.AbsolutePath -notmatch '^/docs/help/home/org_project/pipeline/?') {
                    [void]$assets.Add($assetUri.AbsoluteUri)
                }
            } catch {}
        }
    }
}

foreach ($assetUrl in $assets) {
    try {
        $assetUri = [Uri]$assetUrl
        $path = $assetUri.AbsolutePath.TrimStart('/')
        if ([string]::IsNullOrWhiteSpace($path)) { continue }
        $assetOutput = Join-Path $destination $path
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $assetOutput) | Out-Null
        Invoke-WebRequest -Uri $assetUrl -UseBasicParsing -OutFile $assetOutput
    } catch {
        Write-Warning "Could not download asset: $assetUrl"
    }
}

$rows = $savedPages | ForEach-Object { '<li><a href="' + $_.File + '">' + $_.Url + '</a></li>' }
$index = @"
<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>AtomGit 流水线文档</title></head>
<body><h1>AtomGit 流水线文档</h1><p>下载时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')</p><p>页面数: $($savedPages.Count)</p><ol>$($rows -join [Environment]::NewLine)</ol></body></html>
"@
[System.IO.File]::WriteAllText((Join-Path $destination 'index.html'), $index, [System.Text.UTF8Encoding]::new($false))
$savedPages | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination 'manifest.json') -Encoding UTF8
Write-Output "Saved $($savedPages.Count) pages and $($assets.Count) referenced assets to $destination"
