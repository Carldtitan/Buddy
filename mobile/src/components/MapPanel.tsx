import { AppIcon } from "./AppIcon";
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";

import { colors } from "../theme/colors";
import type { Place } from "../types/contracts";

interface MapPanelProps {
  place: Place;
  query: string;
  onChangeQuery: (value: string) => void;
  phone: string;
  onChangePhone: (value: string) => void;
  onRun: () => void;
  busy: boolean;
}

export function MapPanel({ place, query, onChangeQuery, phone, onChangePhone, onRun, busy }: MapPanelProps) {
  return (
    <View style={styles.wrap}>
      <View style={styles.map}>
        <View style={styles.grid} />
        <View style={styles.route} />
        <View style={[styles.block, styles.blockOne]} />
        <View style={[styles.block, styles.blockTwo]} />
        <View style={[styles.block, styles.blockThree]} />
        <View style={styles.pin}>
          <AppIcon name="MapPin" color={colors.white} size={22} strokeWidth={2.7} />
        </View>
        <View style={styles.coordinateBar}>
          <AppIcon name="Navigation" color={colors.blue} size={14} strokeWidth={2.4} />
          <Text style={styles.coordinateText}>
            {place.latitude?.toFixed(3) ?? "--"} / {place.longitude?.toFixed(3) ?? "--"}
          </Text>
        </View>
      </View>

      <View style={styles.searchDock}>
        <View style={styles.inputRow}>
          <AppIcon name="Search" color={colors.inkMuted} size={18} strokeWidth={2.2} />
          <TextInput
            value={query}
            onChangeText={onChangeQuery}
            placeholder="Place, address, or cross street"
            placeholderTextColor={colors.inkMuted}
            style={styles.input}
            returnKeyType="search"
          />
        </View>
        <View style={styles.inputRow}>
          <AppIcon name="PhoneCall" color={colors.inkMuted} size={18} strokeWidth={2.2} />
          <TextInput
            value={phone}
            onChangeText={onChangePhone}
            placeholder="Venue phone for confirmation call"
            placeholderTextColor={colors.inkMuted}
            style={styles.input}
            keyboardType="phone-pad"
          />
        </View>
        <TouchableOpacity
          accessibilityRole="button"
          disabled={busy}
          onPress={onRun}
          style={[styles.button, busy && styles.buttonDisabled]}
        >
          <Text style={styles.buttonText}>{busy ? "Checking..." : "Run access check"}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.surface,
    borderBottomColor: colors.line,
    borderBottomWidth: StyleSheet.hairlineWidth
  },
  map: {
    backgroundColor: "#DCE8EC",
    height: 292,
    overflow: "hidden"
  },
  grid: {
    ...StyleSheet.absoluteFillObject,
    borderColor: "rgba(39, 94, 121, 0.16)",
    borderWidth: 1,
    transform: [{ rotate: "-8deg" }]
  },
  route: {
    backgroundColor: colors.blue,
    height: 5,
    left: -20,
    opacity: 0.85,
    position: "absolute",
    top: 146,
    transform: [{ rotate: "-18deg" }],
    width: 420
  },
  block: {
    backgroundColor: "rgba(255, 255, 255, 0.72)",
    borderColor: "rgba(39, 94, 121, 0.16)",
    borderWidth: 1,
    position: "absolute"
  },
  blockOne: {
    height: 72,
    left: 28,
    top: 42,
    width: 128
  },
  blockTwo: {
    height: 92,
    right: 26,
    top: 78,
    width: 102
  },
  blockThree: {
    bottom: 32,
    height: 74,
    left: 96,
    width: 150
  },
  pin: {
    alignItems: "center",
    backgroundColor: colors.red,
    borderRadius: 24,
    height: 48,
    justifyContent: "center",
    left: "50%",
    marginLeft: -24,
    marginTop: -24,
    position: "absolute",
    top: "50%",
    width: 48
  },
  coordinateBar: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.line,
    borderRadius: 6,
    borderWidth: 1,
    bottom: 12,
    flexDirection: "row",
    gap: 6,
    left: 12,
    paddingHorizontal: 10,
    paddingVertical: 7,
    position: "absolute"
  },
  coordinateText: {
    color: colors.blue,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0
  },
  searchDock: {
    gap: 10,
    padding: 14
  },
  inputRow: {
    alignItems: "center",
    borderColor: colors.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: "row",
    gap: 9,
    minHeight: 46,
    paddingHorizontal: 12
  },
  input: {
    color: colors.ink,
    flex: 1,
    fontSize: 15,
    fontWeight: "600",
    letterSpacing: 0,
    minWidth: 0
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.black,
    borderRadius: 8,
    height: 48,
    justifyContent: "center"
  },
  buttonDisabled: {
    opacity: 0.56
  },
  buttonText: {
    color: colors.white,
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: 0
  }
});
