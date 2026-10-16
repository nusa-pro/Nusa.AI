// Service worker Nusa AI (versi minimal)
// Tidak menyimpan apa pun di cache dan tidak mengubah permintaan apa pun, jadi chat, login, dan /api
// selalu langsung ke internet. Fungsinya hanya agar Nusa bisa dipasang sebagai aplikasi.
// Kalau perangkat offline, Nusa menampilkan pemberitahuan di teks loading (diatur di index.html).

self.addEventListener("install", () => self.skipWaiting());

self.addEventListener("activate", (event) => {
  // buang cache dari versi lama service worker kalau ada
  event.waitUntil(
    (async () => {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") self.skipWaiting();
});

// handler kosong: permintaan diteruskan apa adanya ke jaringan
self.addEventListener("fetch", () => {});
