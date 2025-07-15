const socket = new WebSocket("ws://localhost:8765");

socket.onmessage = (event) => {
  try {
    const dct = JSON.parse(event.data);

    if (dct.svg) {
      document.getElementById("svg-container").innerHTML = dct.svg;
    }
    if (dct.style) {
      const styleTag = document.createElement("style");
      styleTag.innerHTML = dct.style;
      document.head.appendChild(styleTag);
    }
    if (dct.term) {
      const result = dct.term.replace(/\s+$/, "");
      term.write(result + "\r\n");
    }
    if (dct.term2) {
      const result = dct.term2.replace(/\s+$/, "");
      term2.write(result + "\r\n");
    }
  } catch (e) {
    document.getElementById("svg-container").innerHTML = event.data;
  }
};

socket.onopen = () => {
  console.log("Conectado al WebSocket");
};

socket.onerror = (error) => {
  console.error("WebSocket error:", error);
};

// Terminal principal
const term = new Terminal({
  cols: 80,
  rows: 10,
  fontSize: 22,
  scrollback: 0, 
  theme: {
    background: "#303030",
    foreground: "#ffffff",
  }
});
term.open(document.getElementById("terminal"));
term.write("> Terminal conectada.\r\n");

// Terminal secundario
const term2 = new Terminal({
  cols: 25,
  rows: 10,
  fontSize: 22,
  scrollback: 0, 
  cursorBlink: false,
  disableStdin: true,
  allowProposedApi: true,
  theme: {
    background: "#303030",
    foreground: "#ffffff"
  }
});

term2.open(document.getElementById("terminal2"));
term2.setOption('cursorStyle', 'hidden');
term2.write("Term 2 OK\r\n");

// Hack para ocultar cursor completamente
if (term2._core && term2._core._renderService && term2._core._renderService._cursor) {
  term2._core._renderService._cursor.render = () => {};
}

