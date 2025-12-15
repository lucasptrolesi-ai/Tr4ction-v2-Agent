import "./global.css";
import Providers from "./providers";

export const metadata = {
  title: "TR4CTION Agent",
  description: "Sistema oficial da FCJ Venture Builder"
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-br">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
