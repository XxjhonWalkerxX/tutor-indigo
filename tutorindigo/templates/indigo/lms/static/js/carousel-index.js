// Carrusel de cursos - Index page
(function () {
  var line = document.getElementById("courseLine");
  if (!line) return; // Solo ejecutar si estamos en la página de inicio
  
  var cards = [];
  var speed = 30; // píxeles por segundo
  var position = 0;
  var isPaused = false;
  var gap = 40; // px de separación entre tarjetas
  var lastTime = null;

  function loadCourses() {
    fetch("/api/courses/v1/courses/?page_size=20")
      .then(r => r.json())
      .then(data => {
        var courses = data.results.filter(c => c.start);
        courses.sort((a, b) => new Date(b.start) - new Date(a.start));
        courses = courses.slice(0, 7);

        render(courses);

        // Esperamos un "tick" para que el navegador calcule anchos,
        // y luego duplicamos hasta rellenar el carrusel
        requestAnimationFrame(function () {
          duplicateUntilFull();
          applyDepth();
          requestAnimationFrame(animate);
        });
      });
  }

  function render(list) {
    line.innerHTML = "";
    cards = [];

    list.forEach(function (c) {
      var card = createCard(c);
      // Asegura separación visual
      card.style.marginRight = gap + "px";
      line.appendChild(card);
      cards.push(card);
    });
  }

  // NUEVA función: duplicar hasta que el carrusel tenga suficiente ancho
  function duplicateUntilFull() {
    if (!cards.length) return;

    var cardWidth = cards[0].offsetWidth;
    if (!cardWidth) return;

    // Queremos que el carrusel tenga al menos el doble del ancho de la ventana
    var minWidth = window.innerWidth * 2;
    var totalWidth = cards.length * (cardWidth + gap);

    // Mientras no llenemos ese ancho, seguimos duplicando el set de tarjetas
    while (totalWidth < minWidth) {
      // Hacemos una copia del array actual de cards para no iterar sobre los nuevos mientras los agregamos
      var current = cards.slice();
      current.forEach(function (c) {
        var clone = c.cloneNode(true);

        // Los event listeners NO se copian con cloneNode(true),
        // hay que volver a agregarlos:
        clone.addEventListener("mouseenter", function () { isPaused = true; });
        clone.addEventListener("mouseleave", function () { isPaused = false; });

        line.appendChild(clone);
      });

      cards = Array.from(line.children);
      totalWidth = cards.length * (cardWidth + gap);
    }
  }

  function createCard(course) {
    var card = document.createElement("a");
    card.className = "course-card-mini";
    card.href = "/courses/" + course.course_id + "/about";

    var img = "";
    if (course.media && course.media.course_image && course.media.course_image.uri) {
      img = course.media.course_image.uri;
    } else if (course.media && course.media.image && course.media.image.raw) {
      img = course.media.image.raw;
    }

    card.innerHTML =
      '<div class="card-image" style="width:100%;height:100%;background-image:url(\'' + img + '\');background-size:cover;background-position:center;border-radius:20px;"></div>';

    card.addEventListener("mouseenter", function () { isPaused = true; });
    card.addEventListener("mouseleave", function () { isPaused = false; });

    return card;
  }

  function animate(currentTime) {
    if (!lastTime) {
      lastTime = currentTime;
    }

    var deltaTime = (currentTime - lastTime) / 1000; // convertir a segundos
    lastTime = currentTime;

    if (!isPaused && cards.length) {
      // Movimiento basado en tiempo real para velocidad constante
      position -= speed * deltaTime;

      var cardWidth = cards[0].offsetWidth || 0;
      var totalWidth = cards.length * (cardWidth + gap);

      // Cuando hayamos desplazado la mitad del "cinturón", lo reseteamos
      // porque ya tenemos el patrón repetido
      if (Math.abs(position) >= totalWidth / 2) {
        position = position % (totalWidth / 2);
      }

      line.style.transform = "translateX(" + position + "px)";
      applyDepth();
    }

    requestAnimationFrame(animate);
  }

  function applyDepth() {
    var center = window.innerWidth / 2;

    cards.forEach(function (card) {
      var rect = card.getBoundingClientRect();
      var cardCenter = rect.left + rect.width / 2;
      var dist = Math.abs(center - cardCenter);

      var norm = dist / center;
      if (norm > 1) norm = 1;

      // Ojo: esto escala más cuando está lejos, si quieres efecto contrario
      // invierte la fórmula. Por ahora respeto la tuya.
      var scale = 0.78 + (norm * 0.62);
      var rotate = (cardCenter - center) / 28;
      var translateY = norm * -12;
      var opacity = 0.70 + norm * 0.30;

      card.style.transform =
        "translateY(" + translateY + "px) " +
        "scale(" + scale + ") " +
        "rotateY(" + rotate + "deg)";

      card.style.opacity = opacity;
    });
  }

  loadCourses();
})();
