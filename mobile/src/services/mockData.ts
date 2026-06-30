import type { AccessCheck, AccessCheckCreate, CommunityReport, EvidenceItem } from "../types/contracts";

const now = new Date("2026-06-30T19:25:00.000Z").toISOString();
const tomorrow = new Date("2026-07-01T19:25:00.000Z").toISOString();

export const defaultCreatePayload: AccessCheckCreate = {
  place: {
    query: "Demo Cafe near REDACTED San Francisco",
    phone: "+15555555555",
    latitude: 37.782,
    longitude: -122.392
  },
  needs: {
    step_free_entrance: true,
    accessible_restroom: true,
    wheelchair_seating_or_path: true,
    avoid_temporary_blockers: true,
    notes: "Prefer current, day-of confirmation before travel."
  }
};

const evidence: EvidenceItem[] = [
  {
    id: "3f6b2e3b-7d78-4fb6-9f85-f651af7aa9f1",
    source_type: "photo",
    source_url: "https://images.unsplash.com/photo-1514933651103-005eec06c04b",
    source_timestamp: "2026-06-29T16:20:00.000Z",
    collected_at: now,
    title: "Entrance photo",
    claim: "Street-level front door with a portable ramp visible near the host stand.",
    feature: "entrance",
    polarity: "supports_access",
    confidence: 0.82,
    image_url: "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=900&q=80",
    raw: { provider: "mock" }
  },
  {
    id: "0b279db4-f033-4ba3-ae50-724de7e65a89",
    source_type: "review",
    source_url: "https://example.com/reviews/demo-cafe",
    source_timestamp: "2026-06-12T17:05:00.000Z",
    collected_at: now,
    title: "Recent guest note",
    claim: "The main aisle was wide enough, but patio chairs were tight during lunch.",
    feature: "seating",
    polarity: "unknown",
    confidence: 0.61,
    image_url: null,
    raw: { provider: "mock" }
  },
  {
    id: "e9404b24-422a-4caa-83ac-c218e32b1969",
    source_type: "call",
    source_url: null,
    source_timestamp: now,
    collected_at: now,
    title: "Venue phone confirmation",
    claim: "Staff confirmed a step-free entrance and no construction blockers today.",
    feature: "temporary_blocker",
    polarity: "supports_access",
    confidence: 0.88,
    image_url: null,
    raw: { provider: "twilio" }
  }
];

export const demoCheck: AccessCheck = {
  id: "22e04118-4d6a-4737-9e60-9bcaf142bb4c",
  place: {
    id: "94201e3b-12fb-4da1-b70f-54d86fa7a456",
    name: "Demo Cafe",
    address: "REDACTED, San Francisco, CA",
    phone: "+15555555555",
    website: "https://example.com/demo-cafe",
    latitude: 37.782,
    longitude: -122.392
  },
  needs: defaultCreatePayload.needs,
  stage: "published",
  timeline: [
    {
      stage: "created",
      message: "Accessibility check created.",
      created_at: "2026-06-30T19:21:00.000Z",
      metadata: {}
    },
    {
      stage: "scraping_public_web",
      message: "Collected public web and photo evidence.",
      created_at: "2026-06-30T19:21:08.000Z",
      metadata: {}
    },
    {
      stage: "scoring_evidence",
      message: "Found two supporting claims and one seating caveat.",
      created_at: "2026-06-30T19:21:20.000Z",
      metadata: {}
    },
    {
      stage: "warming_voice_agent",
      message: "Voice agent warmed for current-day confirmation.",
      created_at: "2026-06-30T19:21:35.000Z",
      metadata: {}
    },
    {
      stage: "calling_venue",
      message: "Venue answered and confirmed visit-critical facts.",
      created_at: "2026-06-30T19:22:10.000Z",
      metadata: {}
    },
    {
      stage: "published",
      message: "Final report published.",
      created_at: "2026-06-30T19:23:02.000Z",
      metadata: {}
    }
  ],
  evidence,
  analysis: {
    enough_evidence: false,
    missing_facts: [
      {
        feature: "restroom",
        question: "Is there an accessible customer restroom available today?",
        reason: "Public sources did not provide recent restroom detail.",
        critical: true
      }
    ],
    evidence,
    preliminary_status: "yellow",
    preliminary_summary: "Two supporting accessibility claims found; restroom needed current confirmation."
  },
  call_session: {
    id: "f4937085-df7f-4376-9c29-05e1bce7e95a",
    check_id: "22e04118-4d6a-4737-9e60-9bcaf142bb4c",
    to_phone: "+15555555555",
    from_phone: "+15550000000",
    provider: "twilio",
    status: "completed",
    transcript: [
      {
        speaker: "buddy",
        text: "Hi, I am checking accessibility before someone visits today. Is there a step-free entrance?"
      },
      {
        speaker: "venue",
        text: "Yes, the main entrance is level from the sidewalk, and we keep the doorway clear."
      },
      {
        speaker: "buddy",
        text: "Is there an accessible customer restroom available today?"
      },
      {
        speaker: "venue",
        text: "Yes, it is on the main floor. No code is needed, and there are grab bars."
      },
      {
        speaker: "buddy",
        text: "Any temporary blockers today, like construction or a broken ramp?"
      },
      {
        speaker: "venue",
        text: "No temporary blockers today. Lunch gets crowded, but staff can move chairs."
      }
    ],
    conversation_summary:
      "Buddy confirmed the level entrance, main-floor accessible restroom, and no temporary blockers. Seating may need staff help during the lunch rush.",
    extracted_facts: {
      step_free_entrance: "yes",
      accessible_restroom: "yes",
      wheelchair_seating_or_path: "yes",
      temporary_blockers: [],
      confidence: 0.84,
      notes: "Venue reported staff can move chairs when lunch traffic narrows the route.",
      needs_followup: false
    },
    recording_url: null,
    started_at: "2026-06-30T19:21:45.000Z",
    ended_at: "2026-06-30T19:22:28.000Z"
  },
  final_report: {
    status: "green",
    summary:
      "Demo Cafe is confirmed for the requested visit needs today, with one seating detail to watch during peak lunch.",
    recommendation:
      "Reasonable to visit. Ask staff to clear a path if the main aisle tightens during lunch service.",
    confirmed_facts: [
      "Step-free entrance confirmed by phone",
      "Accessible restroom on the main floor",
      "No temporary blockers reported today"
    ],
    risks: ["Lunch crowd can make movable chairs tighten the path"],
    unknowns: [],
    evidence_ids: evidence.map((item) => item.id),
    evidence,
    voice_conversation_summary:
      "Buddy confirmed the entrance, restroom, seating path, and no temporary blockers with venue staff.",
    voice_transcript: [
      {
        speaker: "buddy",
        text: "Hi, I am checking accessibility before someone visits today. Is there a step-free entrance?"
      },
      {
        speaker: "venue",
        text: "Yes, the main entrance is level from the sidewalk, and we keep the doorway clear."
      },
      {
        speaker: "buddy",
        text: "Is there an accessible customer restroom available today?"
      },
      {
        speaker: "venue",
        text: "Yes, it is on the main floor. No code is needed, and there are grab bars."
      },
      {
        speaker: "buddy",
        text: "Any temporary blockers today, like construction or a broken ramp?"
      },
      {
        speaker: "venue",
        text: "No temporary blockers today. Lunch gets crowded, but staff can move chairs."
      }
    ],
    confidence: 0.84,
    expires_at: tomorrow,
    generated_at: now,
    openui_payload: {
      target: "react-native",
      component: "AccessibilityReport",
      props: {
        place: {
          id: "place-demo-cafe",
          name: "Demo Cafe",
          address: "REDACTED, San Francisco, CA"
        },
        status: "green",
        summary:
          "Demo Cafe is confirmed for the requested visit needs today, with one seating detail to watch during peak lunch.",
        recommendation:
          "Reasonable to visit. Ask staff to clear a path if the main aisle tightens during lunch service.",
        sections: [
          {
            title: "Confirmed",
            items: [
              "Step-free entrance confirmed by phone",
              "Accessible restroom on the main floor",
              "No temporary blockers reported today"
            ]
          },
          {
            title: "Risks",
            items: ["Lunch crowd can make movable chairs tighten the path"]
          },
          {
            title: "Unknowns",
            items: []
          }
        ],
        confidence: 0.84,
        expiresAt: tomorrow
      }
    }
  },
  community_report: null,
  created_at: "2026-06-30T19:21:00.000Z",
  updated_at: now
};

export const demoCommunityReports: CommunityReport[] = [
  {
    id: "8af0c4a1-c60f-4fb0-aea8-846f98af3af1",
    check_id: demoCheck.id,
    place: demoCheck.place,
    status: "green",
    public_summary: "Confirmed level entry, accessible restroom, and no day-of blockers.",
    evidence_summary: "Phone confirmation plus recent entrance photo.",
    voice_conversation_summary: demoCheck.final_report?.voice_conversation_summary ?? null,
    expires_at: tomorrow,
    created_at: now
  },
  {
    id: "13d66438-dcf8-475a-b822-28a260404b71",
    check_id: "b7e3d4cc-0d3c-44f4-aeda-f0df59ac0a45",
    place: {
      id: "06ee36b4-869a-4efd-baf4-11d21037e1cf",
      name: "Market Hall",
      address: "Ferry Building, San Francisco, CA",
      phone: null,
      website: null,
      latitude: 37.7955,
      longitude: -122.3937
    },
    status: "yellow",
    public_summary: "Entrance route looks good; restroom detail still needs a fresh check.",
    evidence_summary: "Map and public web evidence found, no completed call yet.",
    voice_conversation_summary: null,
    expires_at: tomorrow,
    created_at: "2026-06-30T17:10:00.000Z"
  }
];
