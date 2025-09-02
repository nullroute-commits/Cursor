"""
NIST Cybersecurity Framework Compliance Module.

Implements NIST CSF controls and provides compliance reporting.

Last updated: 2025-01-27 by nullroute-commits
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from django.conf import settings
from app.core.audit import AuditLogger

logger = logging.getLogger(__name__)


class NISTFunction(Enum):
    """NIST CSF Functions."""
    IDENTIFY = "IDENTIFY"
    PROTECT = "PROTECT"
    DETECT = "DETECT"
    RESPOND = "RESPOND"
    RECOVER = "RECOVER"


class NISTCategory(Enum):
    """NIST CSF Categories."""
    # IDENTIFY
    ID_AM = "ID.AM"  # Asset Management
    ID_BE = "ID.BE"  # Business Environment
    ID_GV = "ID.GV"  # Governance
    ID_RA = "ID.RA"  # Risk Assessment
    ID_RM = "ID.RM"  # Risk Management Strategy
    ID_SC = "ID.SC"  # Supply Chain Risk Management
    
    # PROTECT
    PR_AC = "PR.AC"  # Access Control
    PR_AT = "PR.AT"  # Awareness and Training
    PR_DS = "PR.DS"  # Data Security
    PR_IP = "PR.IP"  # Information Protection Processes
    PR_MA = "PR.MA"  # Maintenance
    PR_PT = "PR.PT"  # Protective Technology
    
    # DETECT
    DE_AE = "DE.AE"  # Anomalies and Events
    DE_CM = "DE.CM"  # Security Continuous Monitoring
    DE_DP = "DE.DP"  # Detection Processes
    
    # RESPOND
    RS_RP = "RS.RP"  # Response Planning
    RS_CO = "RS.CO"  # Communications
    RS_AN = "RS.AN"  # Analysis
    RS_MI = "RS.MI"  # Mitigation
    RS_IM = "RS.IM"  # Improvements
    
    # RECOVER
    RC_RP = "RC.RP"  # Recovery Planning
    RC_IM = "RC.IM"  # Improvements
    RC_CO = "RC.CO"  # Communications


@dataclass
class NISTControl:
    """NIST CSF Control implementation."""
    id: str
    name: str
    description: str
    function: NISTFunction
    category: NISTCategory
    subcategory: str
    implementation_status: str
    last_assessed: datetime
    next_assessment: datetime
    evidence: List[str]
    notes: Optional[str] = None


class NISTComplianceManager:
    """
    Manages NIST CSF compliance implementation and reporting.
    
    Features:
    - Control implementation tracking
    - Compliance assessment
    - Risk scoring
    - Compliance reporting
    - Audit trail integration
    """
    
    def __init__(self) -> None:
        """Initialize NIST compliance manager."""
        self.audit_logger = AuditLogger()
        self.controls: Dict[str, NISTControl] = {}
        self._initialize_controls()
    
    def _initialize_controls(self) -> None:
        """Initialize NIST CSF controls."""
        # IDENTIFY Function Controls
        self.controls["ID.AM-1"] = NISTControl(
            id="ID.AM-1",
            name="Physical devices and systems within the organization are inventoried",
            description="Maintain inventory of all physical devices and systems",
            function=NISTFunction.IDENTIFY,
            category=NISTCategory.ID_AM,
            subcategory="ID.AM-1",
            implementation_status="IMPLEMENTED",
            last_assessed=datetime.now(timezone.utc),
            next_assessment=datetime.now(timezone.utc),
            evidence=["Asset inventory system", "Regular asset audits"],
            notes="Automated asset discovery implemented"
        )
        
        # PROTECT Function Controls
        self.controls["PR.AC-1"] = NISTControl(
            id="PR.AC-1",
            name="Identities and credentials are issued, managed, verified, revoked, and audited",
            description="Implement comprehensive identity and access management",
            function=NISTFunction.PROTECT,
            category=NISTCategory.PR_AC,
            subcategory="PR.AC-1",
            implementation_status="IMPLEMENTED",
            last_assessed=datetime.now(timezone.utc),
            next_assessment=datetime.now(timezone.utc),
            evidence=["RBAC system", "Multi-factor authentication", "Regular access reviews"],
            notes="RBAC system with audit logging implemented"
        )
        
        # DETECT Function Controls
        self.controls["DE.AE-1"] = NISTControl(
            id="DE.AE-1",
            name="Baseline network operations and expected data flows are established and managed",
            description="Monitor network operations for anomalies",
            function=NISTFunction.DETECT,
            category=NISTCategory.DE_AE,
            subcategory="DE.AE-1",
            implementation_status="PARTIALLY_IMPLEMENTED",
            last_assessed=datetime.now(timezone.utc),
            next_assessment=datetime.now(timezone.utc),
            evidence=["Network monitoring tools"],
            notes="Basic monitoring implemented, advanced analytics pending"
        )
        
        # RESPOND Function Controls
        self.controls["RS.RP-1"] = NISTControl(
            id="RS.RP-1",
            name="Response plan is executed during or after an incident",
            description="Execute incident response plan",
            function=NISTFunction.RESPOND,
            category=NISTCategory.RS_RP,
            subcategory="RS.RP-1",
            implementation_status="IMPLEMENTED",
            last_assessed=datetime.now(timezone.utc),
            next_assessment=datetime.now(timezone.utc),
            evidence=["Incident response plan", "Response team training", "Tabletop exercises"],
            notes="Comprehensive incident response plan in place"
        )
        
        # RECOVER Function Controls
        self.controls["RC.RP-1"] = NISTControl(
            id="RC.RP-1",
            name="Recovery plan is executed during or after an incident",
            description="Execute disaster recovery plan",
            function=NISTFunction.RECOVER,
            category=NISTCategory.RC_RP,
            subcategory="RC.RP-1",
            implementation_status="IMPLEMENTED",
            last_assessed=datetime.now(timezone.utc),
            next_assessment=datetime.now(timezone.utc),
            evidence=["Disaster recovery plan", "Backup systems", "Recovery testing"],
            notes="Regular disaster recovery testing performed"
        )
    
    def assess_control(self, control_id: str, status: str, evidence: List[str], notes: Optional[str] = None) -> bool:
        """
        Assess a specific control implementation.
        
        Args:
            control_id: Control identifier
            status: Implementation status
            evidence: List of evidence items
            notes: Additional notes
        
        Returns:
            True if assessment successful, False otherwise
        """
        if control_id not in self.controls:
            logger.error(f"Control {control_id} not found")
            return False
        
        control = self.controls[control_id]
        control.implementation_status = status
        control.evidence = evidence
        control.notes = notes
        control.last_assessed = datetime.now(timezone.utc)
        
        # Log assessment activity
        self.audit_logger.log_activity(
            action="NIST_CONTROL_ASSESSMENT",
            resource_type="NIST_CONTROL",
            resource_id=control_id,
            new_values={
                "status": status,
                "evidence": evidence,
                "notes": notes,
                "assessed_at": control.last_assessed.isoformat()
            },
            message=f"NIST control {control_id} assessed: {status}"
        )
        
        logger.info(f"NIST control {control_id} assessed: {status}")
        return True
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report.
        
        Returns:
            Compliance report dictionary
        """
        total_controls = len(self.controls)
        implemented = sum(1 for c in self.controls.values() if c.implementation_status == "IMPLEMENTED")
        partially_implemented = sum(1 for c in self.controls.values() if c.implementation_status == "PARTIALLY_IMPLEMENTED")
        not_implemented = sum(1 for c in self.controls.values() if c.implementation_status == "NOT_IMPLEMENTED")
        
        compliance_percentage = (implemented / total_controls) * 100 if total_controls > 0 else 0
        
        # Group controls by function
        function_summary = {}
        for function in NISTFunction:
            function_controls = [c for c in self.controls.values() if c.function == function]
            function_implemented = sum(1 for c in function_controls if c.implementation_status == "IMPLEMENTED")
            function_total = len(function_controls)
            function_percentage = (function_implemented / function_total) * 100 if function_total > 0 else 0
            
            function_summary[function.value] = {
                "total_controls": function_total,
                "implemented": function_implemented,
                "compliance_percentage": function_percentage
            }
        
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_compliance": {
                "total_controls": total_controls,
                "implemented": implemented,
                "partially_implemented": partially_implemented,
                "not_implemented": not_implemented,
                "compliance_percentage": compliance_percentage
            },
            "function_summary": function_summary,
            "controls": [asdict(control) for control in self.controls.values()],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations based on current compliance status."""
        recommendations = []
        
        # Check for controls that need attention
        for control in self.controls.values():
            if control.implementation_status == "NOT_IMPLEMENTED":
                recommendations.append(f"Implement control {control.id}: {control.name}")
            elif control.implementation_status == "PARTIALLY_IMPLEMENTED":
                recommendations.append(f"Complete implementation of control {control.id}: {control.name}")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("All controls are fully implemented. Consider advanced security measures.")
        
        return recommendations
    
    def export_compliance_report(self, format_type: str = "json") -> str:
        """
        Export compliance report in specified format.
        
        Args:
            format_type: Export format (json, csv, pdf)
        
        Returns:
            Exported report content
        """
        report = self.get_compliance_report()
        
        if format_type.lower() == "json":
            import json
            return json.dumps(report, indent=2, default=str)
        elif format_type.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Control ID", "Name", "Function", "Category", "Status", 
                "Last Assessed", "Next Assessment", "Evidence"
            ])
            
            # Write data
            for control in report["controls"]:
                writer.writerow([
                    control["id"],
                    control["name"],
                    control["function"],
                    control["category"],
                    control["implementation_status"],
                    control["last_assessed"],
                    control["next_assessment"],
                    "; ".join(control["evidence"])
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global instance
nist_compliance_manager = NISTComplianceManager()