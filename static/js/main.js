/* ==========================================
   Aerial Flow — Main JavaScript
   ========================================== */

// ---------- Mobile Navigation ----------
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');

    if (toggle && links) {
        toggle.addEventListener('click', function () {
            this.classList.toggle('active');
            links.classList.toggle('open');
        });

        links.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                toggle.classList.remove('active');
                links.classList.remove('open');
            });
        });
    }

    // Инициализируем мини-тест
    initQuiz();
    console.log('Aerial Flow: мини-тест инициализирован');
});

// ---------- Mini Quiz ----------
var quizState = {
    step: 1,
    answers: {}
};

function initQuiz() {
    var steps = document.querySelectorAll('.quiz-step');
    var options = document.querySelectorAll('.quiz-option');
    var progressBar = document.getElementById('quizProgressBar');

    if (!steps.length) return;

    options.forEach(function (opt) {
        opt.addEventListener('click', function () {
            var step = parseInt(this.closest('.quiz-step').dataset.step);
            var value = this.dataset.value;
            quizState.answers[step] = value;

            steps.forEach(function (s) { s.classList.remove('active'); });

            if (step < 3) {
                quizState.step = step + 1;
                var nextStep = document.querySelector('.quiz-step[data-step="' + quizState.step + '"]');
                if (nextStep) nextStep.classList.add('active');

                if (progressBar) {
                    progressBar.style.width = ((quizState.step - 1) / 3 * 100) + '%';
                }
            } else {
                if (progressBar) {
                    progressBar.style.width = '100%';
                }
                showResult();
            }
        });
    });
}

function showResult() {
    var steps = document.querySelectorAll('.quiz-step');
    var result = document.getElementById('quizResult');
    var title = document.getElementById('quizResultTitle');
    var text = document.getElementById('quizResultText');
    var why = document.getElementById('quizResultWhy');
    var icon = document.getElementById('quizResultIcon');

    steps.forEach(function (s) { s.classList.remove('active'); });

    var exp = quizState.answers[1] || 'none';
    var goal = quizState.answers[2] || 'emotions';
    var group = quizState.answers[3] || 'group';

    var resultTitle, resultText, resultWhy, recommendedFormat, resultIcon;

    if (group === 'individual') {
        resultTitle = 'Лучше начать с индивидуального занятия';
        resultText = 'Индивидуальный формат — идеальный выбор для мягкого старта. Вы получите полное внимание преподавателя и программу, построенную под ваш уровень и цели.';
        resultWhy = 'Вы выбрали индивидуальный формат — это значит, что вся программа будет построена лично для вас, с учётом ваших целей и комфортного темпа.';
        recommendedFormat = 'Индивидуальное занятие';
        resultIcon = '🌟';
    } else if (goal === 'flexibility') {
        resultTitle = 'Вам подойдёт воздушное кольцо + пластика';
        resultText = 'Сочетание растяжки и работы на кольце мягко подготовит тело, разовьёт гибкость и подарит ощущение лёгкости.';
        resultWhy = 'Растяжка и кольцо — идеальная пара для тех, кто хочет красивое гибкое тело без силовой нагрузки.';
        recommendedFormat = 'Воздушное кольцо';
        resultIcon = '🌸';
    } else if (exp === 'none' && goal !== 'strength') {
        resultTitle = 'Вам подойдёт мягкий старт на воздушных полотнах';
        resultText = 'Полотна — самый мягкий и женственный формат. Вы начнёте с базовых элементов и постепенно откроете в себе новые возможности.';
        resultWhy = 'Нулевой уровень — не проблема. На полотнах всему учат с самого начала, бережно и с поддержкой.';
        recommendedFormat = 'Воздушные полотна';
        resultIcon = '🦋';
    } else if (goal === 'confidence' || goal === 'emotions') {
        resultTitle = 'Вам подойдёт мягкий старт на воздушных полотнах';
        resultText = 'Полотна дарят невероятное ощущение свободы и полёта. Это помогает почувствовать уверенность в своём теле с первых занятий.';
        resultWhy = 'Воздушные полотна — это про эмоции, свободу и красоту движения. Идеально для нового опыта.';
        recommendedFormat = 'Воздушные полотна';
        resultIcon = '🦋';
    } else {
        resultTitle = 'Вам подойдёт растяжка и мягкая подготовка';
        resultText = 'Начнём с мягкого растяжения, суставной гимнастики и базовых элементов — без спешки и давления.';
        resultWhy = 'С растяжки и пластики начинают многие. Это база, которая подготовит тело к любым элементам в воздухе.';
        recommendedFormat = 'Растяжка и пластика';
        resultIcon = '🌿';
    }

    title.textContent = resultTitle;
    text.textContent = resultText;
    why.textContent = resultWhy;
    if (icon) icon.textContent = resultIcon;

    quizState.recommendedFormat = recommendedFormat;

    result.classList.add('show');
    console.log('Aerial Flow: результат теста —', recommendedFormat);
}

function goToForm() {
    console.log('Aerial Flow: goToForm вызвана');
    var formatSelect = document.getElementById('format');
    var formSection = document.getElementById('contact');
    var formContainer = document.querySelector('.contact-form-container');

    if (formatSelect) {
        console.log('Aerial Flow: select найден', formatSelect);
        if (quizState.recommendedFormat) {
            formatSelect.value = quizState.recommendedFormat;
            console.log('Aerial Flow: установлен формат', quizState.recommendedFormat);
        }
    } else {
        console.log('Aerial Flow: select НЕ НАЙДЕН');
    }

    if (formSection) {
        formSection.scrollIntoView({ behavior: 'smooth' });
        console.log('Aerial Flow: скролл к форме');

        if (formContainer) {
            setTimeout(function () {
                formContainer.classList.add('form-highlight');
                setTimeout(function () {
                    formContainer.classList.remove('form-highlight');
                }, 2000);
            }, 500);
        }
    } else {
        console.log('Aerial Flow: секция contact НЕ НАЙДЕНА');
    }
}

// Делаем goToForm глобальной для onclick
window.goToForm = goToForm;
window.resetQuiz = resetQuiz;

function resetQuiz() {
    quizState.step = 1;
    quizState.answers = {};

    var steps = document.querySelectorAll('.quiz-step');
    var result = document.getElementById('quizResult');
    var progressBar = document.getElementById('quizProgressBar');

    steps.forEach(function (s) { s.classList.remove('active'); });
    var firstStep = document.querySelector('.quiz-step[data-step="1"]');
    if (firstStep) firstStep.classList.add('active');

    if (progressBar) progressBar.style.width = '0%';
    if (result) result.classList.remove('show');
}

// ---------- FAQ Accordion ----------
document.addEventListener('DOMContentLoaded', function () {
    var questions = document.querySelectorAll('.faq-question');
    questions.forEach(function (q) {
        q.addEventListener('click', function () {
            var item = this.closest('.faq-item');
            var isOpen = item.classList.contains('open');

            // Close all
            document.querySelectorAll('.faq-item.open').forEach(function (i) {
                i.classList.remove('open');
            });

            // Open clicked if it was closed
            if (!isOpen) {
                item.classList.add('open');
            }
        });
    });
});

// ---------- Lead Form Submission ----------
document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('leadForm');
    var success = document.getElementById('formSuccess');

    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        var formData = new FormData(form);
        var submitBtn = form.querySelector('button[type="submit"]');
        var originalText = submitBtn.textContent;
        submitBtn.textContent = 'Отправка...';
        submitBtn.disabled = true;

        fetch('/submit-lead', {
            method: 'POST',
            body: formData
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    form.style.display = 'none';
                    success.classList.add('show');
                } else {
                    alert(data.error || 'Произошла ошибка. Попробуйте ещё раз.');
                    submitBtn.textContent = originalText;
                    submitBtn.disabled = false;
                }
            })
            .catch(function () {
                alert('Произошла ошибка. Попробуйте ещё раз.');
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
    });
});

// ---------- Smooth scroll for anchor links ----------
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
