import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource/inter/cyrillic-400.css";
import "@fontsource/inter/cyrillic-500.css";
import "@fontsource/inter/cyrillic-600.css";
import "@fontsource/inter/cyrillic-700.css";
import "@fontsource/inter/latin-400.css";
import "@fontsource/inter/latin-500.css";
import "@fontsource/inter/latin-600.css";
import "@fontsource/inter/latin-700.css";
import "@alfalab/core-components/vars/colors-bluetint.css";
import "@alfalab/core-components/vars/colors-addons.css";
import "@alfalab/core-components/vars/typography-vars.css";
import "@alfalab/core-components/vars/gaps.css";
import "@alfalab/core-components/vars/border-radius.css";
import "@alfalab/core-components/vars/common.css";
import "./styles.css";
import App from "./App";
import { Provider } from "./store";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Provider>
      <App />
    </Provider>
  </React.StrictMode>,
);
