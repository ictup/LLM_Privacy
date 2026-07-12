param(
    [int]$Workers = 32
)

$model = "gpt-5-mini-2025-08-07"
$confirmation = Read-Host (
    "The complete suite can make up to 2,934 paid GPT-5 mini API calls " +
    "with $Workers concurrent workers. " +
    "Type RUN to continue"
)
if ($confirmation -ne "RUN") {
    throw "Interview study suite cancelled before any API call."
}

$secureKey = Read-Host "Enter a NEW OpenAI API key (input is hidden)" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    $env:PYTHONPATH = "src"

    python -m ragshield.evaluation.run_saferag_study `
        --phase all `
        --split all `
        --model $model `
        --judge-model $model `
        --allow-incomplete `
        --workers $Workers
    if ($LASTEXITCODE -ne 0) {
        throw "SafeRAG study did not complete. Rerun the suite to resume."
    }

    python -m ragshield.evaluation.run_synthetic_llm_study `
        --phase all `
        --model $model `
        --workers $Workers
    if ($LASTEXITCODE -ne 0) {
        throw "Controlled canary study did not complete. Rerun the suite to resume."
    }

    python -m ragshield.evaluation.build_interview_report
    if ($LASTEXITCODE -ne 0) {
        throw "Final evidence report generation failed."
    }
}
finally {
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}
