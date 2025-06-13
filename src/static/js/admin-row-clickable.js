document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('tbody tr').forEach(function (row) {        // Ищем первую ссылку в строке
        var link = row.querySelector('th a, td a');
        if (!link) return;

        row.style.cursor = 'pointer';

        row.addEventListener('click', function (e) {
            var tag = e.target.tagName;
            if (tag === 'A' || tag === 'INPUT' || tag === 'LABEL' || e.target.classList.contains('action-select')) {
                return;
            }
            window.location = link.href;
        });
    });
});
