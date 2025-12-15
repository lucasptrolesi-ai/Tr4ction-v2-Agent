export default function FounderLayout({ children }) {
  return (
    <div style={{
      maxWidth: "860px",
      margin: "0 auto",
      padding: "30px"
    }}>
      <header style={{ marginBottom: "20px" }}>
        <h1>TR4CTION Agent – Founder</h1>
      </header>

      {children}
    </div>
  );
}
