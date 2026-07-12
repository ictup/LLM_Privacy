param(
    [string]$Model = "gpt-5.6-luna",
    [int]$LimitPerTask = 2
)

$secureKey = Read-Host "Enter a NEW OpenAI API key (input is hidden)" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
    $env:PYTHONPATH = "src"
    python -m ragshield.evaluation.run_saferag_llm `
        --model $Model `
        --max-output-tokens 512 `
        --limit-per-task $LimitPerTask `
        --case-output "reports/saferag_llm_pilot_cases.jsonl" `
        --json-output "reports/saferag_llm_pilot_summary.json" `
        --markdown-output "reports/saferag_llm_pilot_report.md" `
        --audit-output "reports/saferag_llm_pilot_audit.json"
}
finally {
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
}
