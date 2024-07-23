// 페이지가 로드되면 날짜와 시간 입력의 기본값과 최소값을 현재 날짜와 시간으로 설정
window.onload = function() {
    const minTimeInput = document.getElementById('min_time');
    const maxTimeInput = document.getElementById('max_time');
    const bestTimeInput = document.getElementById('best_time');

    const currentDateTime = getCurrentDateTime();
    minTimeInput.value = currentDateTime;
    minTimeInput.min = currentDateTime;

    // 1시간 이후 시간 계산
    const nowPlusOneHour = new Date(new Date().getTime() + 60 * 60 * 1000);
    const year = nowPlusOneHour.getFullYear();
    const month = String(nowPlusOneHour.getMonth() + 1).padStart(2, '0');
    const day = String(nowPlusOneHour.getDate()).padStart(2, '0');
    const hours = String(nowPlusOneHour.getHours()).padStart(2, '0');
    const minutes = String(nowPlusOneHour.getMinutes()).padStart(2, '0');
    const maxDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;

    maxTimeInput.value = maxDateTime;
    maxTimeInput.min = currentDateTime;
    bestTimeInput.min = currentDateTime;

    // 이벤트 리스너 추가: min_time이 변경될 때마다 max_time 업데이트
    minTimeInput.addEventListener('change', function() {
        const minTimeValue = new Date(minTimeInput.value);
        const updatedMaxTime = new Date(minTimeValue.getTime() + 60 * 60 * 1000);
        const updatedYear = updatedMaxTime.getFullYear();
        const updatedMonth = String(updatedMaxTime.getMonth() + 1).padStart(2, '0');
        const updatedDay = String(updatedMaxTime.getDate()).padStart(2, '0');
        const updatedHours = String(updatedMaxTime.getHours()).padStart(2, '0');
        const updatedMinutes = String(updatedMaxTime.getMinutes()).padStart(2, '0');
        const updatedMaxDateTime = `${updatedYear}-${updatedMonth}-${updatedDay}T${updatedHours}:${updatedMinutes}`;

        maxTimeInput.value = updatedMaxDateTime;
        maxTimeInput.min = minTimeInput.value;
        bestTimeInput.min = minTimeInput.value;
    });
};
