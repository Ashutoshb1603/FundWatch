"""Synthetic FundSnapshot pairs for testing the deterministic core without
needing real factsheet PDFs on disk."""
from src.schema import FundMeta, FundSnapshot, Holding, SectorAllocation, SourceRef


def make_previous() -> FundSnapshot:
    return FundSnapshot(
        document_id="previous",
        fund=FundMeta(
            amc="Example Asset Management",
            scheme_name="Example Flexi Cap Fund",
            plan="Direct",
            option="Growth",
            isin="INF000X01234",
            period="July 2026",
            period_sort_key="2026-07",
        ),
        aum_cr=15100.0,
        aum_source=SourceRef(document_id="previous", page_number=2),
        expense_ratio=0.72,
        expense_ratio_source=SourceRef(document_id="previous", page_number=2),
        riskometer="Moderately High",
        riskometer_source=SourceRef(document_id="previous", page_number=1),
        fund_managers=["Asha Rao"],
        fund_managers_source=SourceRef(document_id="previous", page_number=1),
        holdings=[
            Holding("Reliance Industries", 8.2, SourceRef("previous", 5)),
            Holding("HDFC Bank", 6.9, SourceRef("previous", 5)),
            Holding("Infosys", 5.1, SourceRef("previous", 5)),
            Holding("ICICI Bank", 4.8, SourceRef("previous", 5)),
            Holding("Tata Consultancy Services", 4.0, SourceRef("previous", 5)),
            Holding("Bharti Airtel", 2.1, SourceRef("previous", 5)),
        ],
        sectors=[
            SectorAllocation("Financial Services", 31.4, SourceRef("previous", 8)),
            SectorAllocation("Information Technology", 15.0, SourceRef("previous", 8)),
            SectorAllocation("Energy", 9.5, SourceRef("previous", 8)),
        ],
    )


def make_current() -> FundSnapshot:
    return FundSnapshot(
        document_id="current",
        fund=FundMeta(
            amc="Example Asset Management",
            scheme_name="Example Flexi Cap Fund",
            plan="Direct",
            option="Growth",
            isin="INF000X01234",
            period="August 2026",
            period_sort_key="2026-08",
        ),
        aum_cr=15460.0,
        aum_source=SourceRef(document_id="current", page_number=2),
        expense_ratio=0.68,
        expense_ratio_source=SourceRef(document_id="current", page_number=2),
        riskometer="Moderately High",
        riskometer_source=SourceRef(document_id="current", page_number=1),
        fund_managers=["Asha Rao", "Vikram Seth"],
        fund_managers_source=SourceRef(document_id="current", page_number=1),
        holdings=[
            Holding("Reliance Industries", 6.7, SourceRef("current", 5)),
            Holding("HDFC Bank", 6.9, SourceRef("current", 5)),
            Holding("Infosys", 5.1, SourceRef("current", 5)),
            Holding("ICICI Bank", 5.6, SourceRef("current", 5)),
            Holding("Larsen & Toubro", 3.9, SourceRef("current", 5)),  # new top-10 entrant
            Holding("Bharti Airtel", 2.1, SourceRef("current", 5)),
            # Tata Consultancy Services exited
        ],
        sectors=[
            SectorAllocation("Financial Services", 27.8, SourceRef("current", 8)),
            SectorAllocation("Information Technology", 18.4, SourceRef("current", 8)),
            SectorAllocation("Energy", 9.6, SourceRef("current", 8)),
        ],
    )
