const downloadDestination = import.meta.env.VITE_DOWNLOAD_URL?.trim()
if (downloadDestination) {
  const siteRoot = new URL(import.meta.env.BASE_URL, location.origin)
  const downloadURL = new URL(downloadDestination, siteRoot).href
  for (const action of document.querySelectorAll('[data-get]')) action.href = downloadURL
}

// Move the keyboard reading position with an in-page jump and keep the fragment shareable.
for (const link of document.querySelectorAll('a[href^="#"]')) {
  link.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
    const target = document.getElementById(link.hash.slice(1))
    if (!target) return
    event.preventDefault()
    if (location.hash !== link.hash) history.pushState(null, '', link.hash)
    target.focus({ preventScroll: true })
    target.scrollIntoView()
  })
}

const zoomButton = document.querySelector('[data-zoom]')
const lightbox = document.getElementById('lightbox')
const viewport = lightbox.querySelector('.image-scroll')

const fullImage = new Image()
viewport.append(fullImage)
const imageTitle = lightbox.querySelector('#lightbox-title')
const imageCaption = lightbox.querySelector('#capture-caption')
let focusPoint = { x: 0.5, y: 0.5 }

function centerDetail() {
  if (lightbox.hasAttribute('data-zoomed')) {
    viewport.scrollTo(
      fullImage.offsetWidth * focusPoint.x - viewport.clientWidth / 2,
      fullImage.offsetHeight * focusPoint.y - viewport.clientHeight / 2,
    )
  }
}
fullImage.addEventListener('load', () => {
  fullImage.style.setProperty('--source-width', fullImage.naturalWidth + 'px')
  centerDetail()
})

function setZoom(zoomed) {
  lightbox.toggleAttribute('data-zoomed', zoomed)
  zoomButton.setAttribute('aria-pressed', String(zoomed))
  zoomButton.textContent = zoomed ? 'Fit window' : 'Zoom in'
  if (zoomed) centerDetail()
  else viewport.scrollTo(0, 0)
}

function openCapture(opener) {
  const figure = opener.closest('figure')
  fullImage.alt = opener.querySelector('img').alt
  fullImage.src = opener.href
  imageTitle.textContent = opener.dataset.title
  imageCaption.textContent = figure.querySelector('figcaption').textContent
  focusPoint = { x: Number(opener.dataset.focusX), y: Number(opener.dataset.focusY) }
  setZoom(false)
}

zoomButton.addEventListener('click', () => setZoom(!lightbox.hasAttribute('data-zoomed')))

for (const opener of document.querySelectorAll('[data-open]')) {
  const dialog = document.getElementById(opener.dataset.open)
  opener.setAttribute('aria-haspopup', 'dialog')
  opener.setAttribute('aria-controls', dialog.id)
  opener.addEventListener('click', event => {
    event.preventDefault()
    if (dialog === lightbox) openCapture(opener)
    dialog.showModal()
    dialog.addEventListener('close', () => opener.focus({ preventScroll: true }), { once: true })
  })
}
for (const dialog of document.querySelectorAll('dialog')) {
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close())
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return
    const bounds = dialog.getBoundingClientRect()
    const outside = event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom
    if (outside) dialog.close()
  })
}

if ('IntersectionObserver' in window) {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)')
  const toggle = document.querySelector('.motion-toggle')
  const videos = document.querySelectorAll('video[data-loop]')
  const visible = new Set()
  let paused = false

  function updateIcons() {
    const playing = !paused && !document.hidden && !reducedMotion.matches
    for (const video of videos) {
      if (reducedMotion.matches) video.parentElement.classList.remove('has-frame')
      if (!playing || !visible.has(video)) {
        if (!video.paused) video.pause()
      } else if (video.paused && !video.error) {
        if (!video.hasAttribute('src')) video.src = video.dataset.loop
        video.play().catch(error => {
          if (error.name === 'NotAllowedError' && !document.hidden && visible.has(video)) {
            paused = true
            updateIcons()
          }
        })
      }
    }
    toggle.hidden = reducedMotion.matches
    toggle.textContent = paused ? 'Play' : 'Pause'
    toggle.setAttribute('aria-label', paused ? 'Play icon animations' : 'Pause icon animations')
  }

  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) visible.add(entry.target)
      else visible.delete(entry.target)
    }
    updateIcons()
  })
  for (const video of videos) {
    const art = video.parentElement
    const poster = art.querySelector('img')
    video.style.setProperty('--silhouette', 'url("' + poster.src + '")')
    video.addEventListener('playing', () => {
      if (!reducedMotion.matches) art.classList.add('has-frame')
    })
    video.addEventListener('error', () => art.classList.remove('has-frame'))
    observer.observe(video)
  }
  toggle.addEventListener('click', () => {
    paused = !paused
    updateIcons()
  })
  reducedMotion.addEventListener('change', updateIcons)
  document.addEventListener('visibilitychange', updateIcons)
  updateIcons()
}
