import type { FinalReport, OpenUiPayload, Place, RenderPayloadSection } from "../types/contracts";

export interface LocalReportRenderModel {
  component: "AccessibilityReport";
  placeName: string;
  placeAddress?: string | null;
  status: FinalReport["status"];
  summary: string;
  recommendation: string;
  sections: RenderPayloadSection[];
  confidence: number;
  expiresAt: string;
}

function placeNameFrom(value: unknown): string {
  const place = value as Partial<Place> | undefined;
  return place?.name || "Selected place";
}

function placeAddressFrom(value: unknown): string | null | undefined {
  const place = value as Partial<Place> | undefined;
  return place?.address;
}

export function buildRenderPayload(report: FinalReport, place: Place): OpenUiPayload {
  return (
    report.openui_payload ?? {
      target: "react-native",
      component: "AccessibilityReport",
      props: {
        place,
        status: report.status,
        summary: report.summary,
        recommendation: report.recommendation,
        sections: [
          { title: "Confirmed", items: report.confirmed_facts },
          { title: "Risks", items: report.risks },
          { title: "Unknowns", items: report.unknowns }
        ],
        confidence: report.confidence,
        expiresAt: report.expires_at
      }
    }
  );
}

export function renderPayloadToModel(payload: OpenUiPayload, fallback: FinalReport): LocalReportRenderModel {
  const props = payload.props ?? {};
  const sections =
    Array.isArray(props.sections) && props.sections.length > 0
      ? props.sections
      : [
          { title: "Confirmed", items: fallback.confirmed_facts },
          { title: "Risks", items: fallback.risks },
          { title: "Unknowns", items: fallback.unknowns }
        ];

  return {
    component: "AccessibilityReport",
    placeName: placeNameFrom(props.place),
    placeAddress: placeAddressFrom(props.place),
    status: props.status ?? fallback.status,
    summary: props.summary ?? fallback.summary,
    recommendation: props.recommendation ?? fallback.recommendation,
    sections,
    confidence: typeof props.confidence === "number" ? props.confidence : fallback.confidence,
    expiresAt: props.expiresAt ?? fallback.expires_at
  };
}
