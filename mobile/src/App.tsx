import { StatusBar } from "react-native";
import { SafeAreaView, StyleSheet } from "react-native";

import { HomeScreen } from "./screens/HomeScreen";
import { colors } from "./theme/colors";

export default function App() {
  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.canvas} />
      <HomeScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    backgroundColor: colors.canvas,
    flex: 1
  }
});
