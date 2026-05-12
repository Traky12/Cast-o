import { useParams } from "react-router-dom";
import HidroponicControl from "./pages/HidroponicControl.jsx";

export default function App() {
  const { zoneId } = useParams();
  return <HidroponicControl zoneId={zoneId || "zone_cannabis_1"} />;
}
