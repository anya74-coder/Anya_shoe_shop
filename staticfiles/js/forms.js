// Общая логика для форм
console.log('Forms JS loaded from class Media');

document.addEventListener('DOMContentLoaded', function() {
    // Добавляем валидацию в реальном времени
    const priceInput = document.querySelector('input[name="price"]');
    if (priceInput) {
        priceInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value <= 0) {
                this.setCustomValidity('Цена должна быть больше нуля');
            } else {
                this.setCustomValidity('');
            }
        });
    }
});