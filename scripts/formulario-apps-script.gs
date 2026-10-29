// BULLET · formulario de contacto de la web
// Cada envío manda un mail a admin@ y queda anotado en la hoja "Contactos".
// Proyecto de Apps Script en la cuenta admin@bulletcreativeagency.com; escribe en la planilla "Contactos web BULLET".
// Implementar → Nueva implementación → Tipo "Aplicación web", Ejecutar como "Yo", Acceso "Cualquier persona".
// Copiar la URL /exec y pegarla en FORM_URL (index.html).

const DESTINO = 'admin@bulletcreativeagency.com';
const PLANILLA = '1DBWGSgTvh7VcJp8zPwsqhYT_cdUmRm8erPgCTYFKiPk';   // "Contactos web BULLET"
const HOJA = 'Contactos';
const CAMPOS = ['Nombre', 'Empresa', 'email', 'Teléfono', 'Servicio', 'Mensaje'];

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p._honey) return ContentService.createTextOutput('ok');   // bot: se descarta sin avisar

  const d = {};
  CAMPOS.forEach(c => d[c] = String(p[c] || '').trim().slice(0, c === 'Mensaje' ? 3000 : 120));
  if (!d.Nombre || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email) || !d.Mensaje) {
    return ContentService.createTextOutput('falta');
  }

  guardar(d);

  const filas = CAMPOS.filter(c => d[c]).map(c =>
    `<tr><td style="padding:8px 14px;background:#F4F0ED;font-weight:bold">${c === 'email' ? 'Email' : c}</td>` +
    `<td style="padding:8px 14px">${escapar(d[c]).replace(/\n/g, '<br>')}</td></tr>`).join('');
  MailApp.sendEmail({
    to: DESTINO,
    replyTo: d.email,
    name: 'Web BULLET',
    subject: `Nuevo contacto web: ${d.Nombre}${d.Empresa ? ' (' + d.Empresa + ')' : ''}`,
    htmlBody: `<p style="font-family:Arial">Llegó una consulta desde la web. Respondé este mail para contestarle directo.</p>` +
      `<table style="font-family:Arial;font-size:14px;border-collapse:collapse">${filas}</table>`
  });
  return ContentService.createTextOutput('ok');
}

function guardar(d) {
  const ss = SpreadsheetApp.openById(PLANILLA);
  let hoja = ss.getSheetByName(HOJA);
  if (!hoja) {
    hoja = ss.insertSheet(HOJA);
    hoja.appendRow(['Fecha', 'Nombre', 'Empresa', 'Email', 'Teléfono', 'Servicio', 'Mensaje']);
    hoja.getRange(1, 1, 1, 7).setFontWeight('bold').setBackground('#F4F0ED');
    hoja.setFrozenRows(1);
  }
  // un apóstrofo adelante para que Sheets no interprete los textos como fórmulas
  hoja.appendRow([new Date()].concat(CAMPOS.map(c => d[c] ? "'" + d[c] : '')));
}

function escapar(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Correr UNA vez desde el editor (botón Ejecutar) para dar los permisos de mail y planilla
// y comprobar que llega el mail de prueba.
function probar() {
  doPost({ parameter: { Nombre: 'Prueba', email: DESTINO, Mensaje: 'Mail de prueba del formulario de la web.' } });
}
