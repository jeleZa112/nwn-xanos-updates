// ROBLOX_BG_AI USB HID bridge for Arduino Leonardo / Micro (ATmega32U4).
// Dedicated, user-controlled USB mouse. No background key injection.
// Flash only to boards with native USB HID, NOT Arduino Uno R3/Nano classic.
#include <Mouse.h>
#include <string.h>
#include <stdlib.h>

static const unsigned long BAUD = 115200;
static const unsigned long LEASE_MS = 5000UL;
static const unsigned long MIN_CLICK_INTERVAL_MS = 180UL;
static char lineBuf[48];
static byte lineLen = 0;
static bool armed = false;
static unsigned long lastCommand = 0;
static unsigned long lastClick = 0;

static void disarm() {
  Mouse.release(MOUSE_LEFT);
  armed = false;
}

static void handle(char *cmd) {
  if (strcmp(cmd, "HELLO") == 0) {
    Serial.println(F("ROBLOX_HID_V1"));
    return;
  }
  if (strcmp(cmd, "ARM ROBLOX_HID_V1") == 0) {
    disarm();
    armed = true;
    lastCommand = millis();
    Serial.println(F("OK ARMED"));
    return;
  }
  if (strcmp(cmd, "DISARM") == 0 || strcmp(cmd, "STOP") == 0) {
    disarm();
    Serial.println(F("OK DISARMED"));
    return;
  }
  if (!armed) {
    Serial.println(F("ERR NOT_ARMED"));
    return;
  }
  if (strcmp(cmd, "PING") == 0) {
    lastCommand = millis();
    Serial.println(F("OK PONG"));
    return;
  }
  if (strncmp(cmd, "MOVE ", 5) == 0) {
    char *end1;
    long dx = strtol(cmd + 5, &end1, 10);
    if (end1 == cmd + 5 || *end1 != ' ') {
      Serial.println(F("ERR MOVE_ARGS"));
      return;
    }
    char *end2;
    long dy = strtol(end1 + 1, &end2, 10);
    if (end2 == end1 + 1 || *end2 != '\0' ||
        dx < -100 || dx > 100 || dy < -100 || dy > 100) {
      Serial.println(F("ERR MOVE_RANGE"));
      return;
    }
    lastCommand = millis();
    Mouse.move((int8_t)dx, (int8_t)dy, 0);
    Serial.println(F("OK MOVE"));
    return;
  }
  if (strcmp(cmd, "CLICK") == 0) {
    unsigned long now = millis();
    if (lastClick != 0 && now - lastClick < MIN_CLICK_INTERVAL_MS) {
      Serial.println(F("ERR CLICK_RATE"));
      return;
    }
    lastCommand = now;
    lastClick = now;
    Mouse.press(MOUSE_LEFT);
    delay(85);
    Mouse.release(MOUSE_LEFT);
    Serial.println(F("OK CLICK"));
    return;
  }
  Serial.println(F("ERR UNKNOWN"));
}

void setup() {
  Serial.begin(BAUD);
  Mouse.begin();
  disarm();
  // No action until a deliberate ARM command is received over USB serial.
}

void loop() {
  if (armed && millis() - lastCommand > LEASE_MS) {
    disarm();
    Serial.println(F("ERR LEASE_EXPIRED"));
  }
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      if (lineLen) handle(lineBuf);
      lineLen = 0;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    } else {
      lineLen = 0;
      disarm();
      Serial.println(F("ERR LINE_TOO_LONG"));
    }
  }
}
