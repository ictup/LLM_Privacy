param(
    [ValidateSet("dry-run", "generate", "judge", "report", "all")]
    [string]$Phase = "all",
    [ValidateSet("development", "confirmatory", "all")]
    [string]$Split = "all",
    [int]$Workers = 4
)

$model = "gpt-5-mini-2025-08-07"
$env:PYTHONPATH = "src"

if ($Phase -eq "dry-run" -or $Phase -eq "report") {
    try {
        python -m ragshield.evaluation.run_saferag_study `
            --phase $Phase `
            --split $Split `
            --model $model `
            --judge-model $model `
            --workers $Workers
    }
    finally {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    exit $LASTEXITCODE
}

$confirmation = Read-Host (
    "This run can make up to 2,322 paid GPT-5 mini API calls for all 387 cases. " +
    "Type RUN to continue"
)
if ($confirmation -ne "RUN") {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    throw "Study cancelled before any API call."
}

$secureKey = Read-Host "Enter a NEW OpenAI API key (input is hidden)" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    python -m ragshield.evaluation.run_saferag_study `
        --phase $Phase `
        --split $Split `
        --model $model `
        --judge-model $model `
        --workers $Workers
}
finally {
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}
