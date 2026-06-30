import { useEffect, useMemo, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View
} from "react-native";
import { AppIcon } from "../components/AppIcon";

import { CallSummary } from "../components/CallSummary";
import { CommunityFeed } from "../components/CommunityFeed";
import { EvidenceStrip } from "../components/EvidenceStrip";
import { LocalReportRenderer } from "../components/LocalReportRenderer";
import { MapPanel } from "../components/MapPanel";
import { MissionTimeline } from "../components/MissionTimeline";
import { NeedToggles } from "../components/NeedToggles";
import { TranscriptView } from "../components/TranscriptView";
import { buddyApi } from "../services/api";
import { defaultCreatePayload, demoCheck } from "../services/mockData";
import { colors } from "../theme/colors";
import type { AccessCheck, AccessNeeds, CommunityReport } from "../types/contracts";

export function HomeScreen() {
  const [query, setQuery] = useState(defaultCreatePayload.place.query);
  const [phone, setPhone] = useState(defaultCreatePayload.place.phone ?? "");
  const [needs, setNeeds] = useState<AccessNeeds>(defaultCreatePayload.needs);
  const [check, setCheck] = useState<AccessCheck>(demoCheck);
  const [community, setCommunity] = useState<CommunityReport[]>([]);
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transcript = check.final_report?.voice_transcript ?? check.call_session?.transcript ?? [];
  const evidence = check.final_report?.evidence?.length ? check.final_report.evidence : check.evidence;

  const payload = useMemo(
    () => ({
      place: {
        query,
        phone: phone || null,
        latitude: check.place.latitude,
        longitude: check.place.longitude
      },
      needs
    }),
    [check.place.latitude, check.place.longitude, needs, phone, query]
  );

  async function loadCommunity() {
    const reports = await buddyApi.listCommunityReports();
    setCommunity(reports);
  }

  async function runCheck() {
    setBusy(true);
    setError(null);
    try {
      const next = await buddyApi.createCheck(payload);
      setCheck(next);
      await loadCommunity();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Buddy could not complete the check.");
    } finally {
      setBusy(false);
    }
  }

  async function refresh() {
    setRefreshing(true);
    setError(null);
    try {
      await loadCommunity();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Buddy could not refresh community reports.");
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadCommunity().catch((caught) => {
      setError(caught instanceof Error ? caught.message : "Buddy could not load community reports.");
    });
  }, []);

  return (
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.keyboard}>
      <ScrollView
        style={styles.screen}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} tintColor={colors.blue} />}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.brand}>Buddy</Text>
            <Text style={styles.subhead}>Live access confirmation</Text>
          </View>
          <View style={styles.mode}>
            {buddyApi.hasLiveApi ? (
              <AppIcon name="Wifi" color={colors.green} size={16} strokeWidth={2.4} />
            ) : (
              <AppIcon name="WifiOff" color={colors.yellow} size={16} strokeWidth={2.4} />
            )}
            <Text style={styles.modeText}>{buddyApi.hasLiveApi ? "Live API" : "Local demo"}</Text>
          </View>
        </View>

        <MapPanel
          place={check.place}
          query={query}
          onChangeQuery={setQuery}
          phone={phone}
          onChangePhone={setPhone}
          onRun={runCheck}
          busy={busy}
        />
        <NeedToggles needs={needs} onChange={setNeeds} />

        {error ? (
          <View style={styles.error}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        <MissionTimeline events={check.timeline} currentStage={check.stage} />
        <LocalReportRenderer check={check} />
        <EvidenceStrip evidence={evidence} />
        <CallSummary call={check.call_session} />
        <TranscriptView turns={transcript} />
        <CommunityFeed reports={community} />

        <TouchableOpacity accessibilityRole="button" onPress={refresh} style={styles.refreshButton}>
          <AppIcon name="RefreshCw" color={colors.ink} size={17} strokeWidth={2.4} />
          <Text style={styles.refreshText}>Refresh feed</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboard: {
    flex: 1
  },
  screen: {
    backgroundColor: colors.canvas,
    flex: 1
  },
  content: {
    paddingBottom: 28
  },
  header: {
    alignItems: "center",
    backgroundColor: colors.canvas,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 14
  },
  brand: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0
  },
  subhead: {
    color: colors.inkMuted,
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 0,
    marginTop: 1
  },
  mode: {
    alignItems: "center",
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: 6,
    minHeight: 34,
    paddingHorizontal: 9
  },
  modeText: {
    color: colors.ink,
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 0
  },
  error: {
    backgroundColor: colors.redSoft,
    marginHorizontal: 14,
    marginTop: 10,
    padding: 10,
    borderRadius: 8
  },
  errorText: {
    color: colors.red,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0,
    lineHeight: 18
  },
  refreshButton: {
    alignItems: "center",
    alignSelf: "center",
    borderColor: colors.lineStrong,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: 8,
    height: 42,
    justifyContent: "center",
    marginTop: 4,
    paddingHorizontal: 14
  },
  refreshText: {
    color: colors.ink,
    fontSize: 14,
    fontWeight: "900",
    letterSpacing: 0
  }
});
