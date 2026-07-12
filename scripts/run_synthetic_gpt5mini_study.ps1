param(
    [ValidateSet("dry-run", "run", "report", "all")]
    [string]$Phase = "all",
    [int]$Workers = 32
)

$model = "gpt-5-mini-2025-08-07"
$env:PYTHONPATH = "src"

if ($Phase -eq "dry-run" -or $Phase -eq "report") {
    try {
        python -m ragshield.evaluation.run_synthetic_llm_study `
            --phase $Phase `
            --model $model `
            --workers $Workers
    }
    finally {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    exit $LASTEXITCODE
}

$confirmation = Read-Host (
    "This controlled canary study can make up to 612 paid GPT-5 mini API calls " +
    "with $Workers concurrent workers. Type RUN to continue"
)
if ($confirmation -ne "RUN") {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    throw "Controlled canary study cancelled before any API call."
}

$secureKey = Read-Host "Enter a NEW OpenAI API key (input is hidden)" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    python -m ragshield.evaluation.run_synthetic_llm_study `
        --phase $Phase `
        --model $model `
        --workers $Workers
}
finally {
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}
