class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.maxRetries = options.maxRetries || 5;
    this.baseRetryDelay = options.retryDelay || 2000;
    this.retriesLeft = this.maxRetries;
    this.socket = null;
    this.connected = false;
    this.connect();
  }

  connect() {
    this.socket = new WebSocket(this.url);

    this.socket.onopen = () => {
      this.connected = true;
      this.retriesLeft = this.maxRetries;
      console.log("WebSocket connected");
      term.write("WebSocket connected\n");
    };

    this.socket.onmessage = (event) => this.handleMessage(event);

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error);
      term.write("WebSocket error event\n");
    };

    this.socket.onclose = () => {
      this.connected = false;
      term.write("WebSocket closed\n");

      if (this.retriesLeft > 0) {
        const retryDelay = this.baseRetryDelay * (this.maxRetries - this.retriesLeft + 1);
        term.write(`Retrying in ${retryDelay / 1000} seconds... (${this.retriesLeft} attempts left)\n`);
        console.log(`Retrying in ${retryDelay}ms`);

        setTimeout(() => {
          this.retriesLeft--;
          this.connect();
        }, retryDelay);
      } else {
        term.write("Max retries reached. Could not reconnect.\n");
        console.log("Max retries reached. Stopping reconnection.");
      }
    };
  }

  handleMessage(event) {
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
  }

  send(data) {
    if (this.connected) {
      this.socket.send(data);
    } else {
      console.warn("Cannot send message: not connected.");
    }
  }
}

// Crear instancia WebSocket con reconexión automática
const wsClient = new ReconnectingWebSocket("ws://localhost:8765", {
  maxRetries: 5,
  retryDelay: 2000  // Milisegundos
});

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
term.write("Terminal activa\r\n");

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

// Hack para ocultar cursor completamente
if (term2._core && term2._core._renderService && term2._core._renderService._cursor) {
  term2._core._renderService._cursor.render = () => {};
}

