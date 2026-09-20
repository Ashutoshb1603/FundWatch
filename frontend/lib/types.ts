export type Priority = "HIGH" | "MEDIUM" | "LOW";

export interface Evidence {
  document_id: string;
  page_number: number | null;
  confidence: string;
  extraction_method?: string;
  raw_snippet?: string | null;
}

export interface Finding {
  change_type: string;
  label: string;
  previous_value: number | string | null;
  current_value: number | string | null;
  absolute_difference: number | null;
  percentage_point_difference: number | null;
  priority: Priority;
  rule_triggered: string | null;
  explanation: string | null;
  previous_evidence?: Evidence;
  current_evidence?: Evidence;
}

export interface Brief {
  scheme_name: string | null;
  previous_period: string | null;
  current_period: string | null;
  key_changes: Finding[];
  narrative: string | null;
  narrative_available: boolean;
  caveat: string;
}

export interface StepLog {
  step: string;
  status: string;
  detail?: string;
}

export interface ScanResult {
  scan_id: string;
  status: "processing" | "completed" | "validation_failed" | "error";
  current_step?: string;
  error: string | null;
  fund: {
    scheme_name: string | null;
    amc: string | null;
    previous_period: string | null;
    current_period: string | null;
  };
  validation: {
    same_fund: boolean;
    comparable_periods: boolean;
    periods_consecutive: boolean | null;
    issues: string[];
  } | null;
  extraction: {
    previous_confidence: string | null;
    current_confidence: string | null;
    previous_warnings: string[];
    current_warnings: string[];
  };
  findings: Finding[];
  material_change_count: number;
  brief: Brief | null;
  steps_log: StepLog[];
}
