async function fetchClanker(address) {
    const backendURL = "http://localhost:1214"; // 백엔드 URL

    try {
        const response = await fetch(`${backendURL}/api/token/${address}`);
        if (!response.ok) throw new Error("Failed to fetch clanker");
        const data = await response.json();

        // 위쪽 토큰 정보 설정
        document.querySelector('.token-name').innerHTML = `${data.name} <span class="token-symbol">(${data.symbol})</span>`;
        document.querySelector('.requestor').textContent = `Requestor: ${data.requestor}`;
        document.querySelector('#token-address').textContent = address;
        document.querySelector('.market-value').textContent = `$${data.market_cap}`;
        document.querySelector('.description').textContent = data.description;
        document.querySelector('.token-image').src = data.image_url;

        // 스왑 UI의 "Sell" 토큰 이름 설정
        document.querySelector('#sell-token-name').textContent = data.symbol; // API에서 심볼 제공
        document.querySelector('#buy-token-name').textContent = "WEMIX$"; // WemixDollar 심볼로 설정

        // 초기 스왑 토큰 환율 설정
        buyTokenPrice = 1; // WemixDollar는 항상 $1로 고정
        sellTokenPrice = 1; // 예: 다른 토큰 가격

        // 초기 가격 계산
        updatePrices();
        updateDescription("WEMIX$");

    } catch (error) {
        document.getElementById('content').innerText = "Error fetching clanker: " + error.message;
    }
}

function updatePrices() {
    const buyInput = parseFloat(document.querySelector('#buy-input').value) || 0; // 사용자가 입력한 Buy 값
    const sellAmount = buyInput * buyTokenPrice / sellTokenPrice; // Sell 수량 계산
    const sellValue = sellAmount * sellTokenPrice; // Sell 달러 계산

    // 화면에 업데이트
    document.querySelector('.buy-value').textContent = `$${(buyInput * buyTokenPrice).toFixed(2)}`; // Buy 달러 표시

    document.querySelector('.sell-amount').textContent = `${sellAmount.toFixed(2)} Tokens`; // Sell 토큰 수량 표시
    document.querySelector('.sell-value').textContent = `$${sellValue.toFixed(2)}`; // Sell 달러 표시
}

function swapTokens() {
    // "Sell"과 "Buy" 토큰 이름 교환
    const sellToken = document.querySelector('#sell-token-name');
    const buyToken = document.querySelector('#buy-token-name');

    const tempName = sellToken.textContent;
    sellToken.textContent = buyToken.textContent;
    buyToken.textContent = tempName;

    // 가격은 WemixDollar는 항상 $1이므로 "Sell"의 가격만 교환
    if (buyToken.textContent === "WEMIX$") {
        buyTokenPrice = 1;
        sellTokenPrice = 1;
    } else {
        sellTokenPrice = 1; // 현재 "Sell" 토큰 가격
        buyTokenPrice = 1; // "Buy" 토큰 가격은 WemixDollar로 고정
    }

    // 문구 업데이트
    updateDescription(buyToken.textContent);

    // 가격 업데이트
    updatePrices();
}

function updateDescription(buyTokenName) {
    const descriptionElement = document.querySelector('.swap-description');
    descriptionElement.textContent = `Swap your ${buyTokenName} securely and instantly.`;
}


function openWemixScan() {
    const tokenAddress = document.querySelector('#token-address').textContent;
    const wemixScanUrl = `https://testnet.wemixscan.com/address/${tokenAddress}`;
    window.open(wemixScanUrl, '_blank'); // 새 탭에서 URL 열기
}

function openWemixPlay() {
    const wemixPlayUrl = "https://wemixplay.com/";
    window.open(wemixPlayUrl, "_blank"); // 새 탭에서 WemixPlay 메인 페이지 열기
}

// URL에서 토큰 주소 추출
function getTokenAddressFromURL() {
    const pathSegments = window.location.pathname.split('/'); // 경로를 '/'로 나누기
    return pathSegments[pathSegments.length - 1] || "0x2f5E79469EbFfA1Ea73030cb23eB921C7BcB7091"; // 마지막 경로를 토큰 주소로 사용
}

// 페이지 로드 시 데이터 로드
window.onload = () => {
    // URL에서 토큰 주소 가져오기
    const tokenAddress = getTokenAddressFromURL();

    // 토큰 데이터 가져오기
    fetchClanker(tokenAddress);

    // Buy 입력 필드 변경 시 가격 업데이트
    document.querySelector('#buy-input').addEventListener('input', updatePrices);

    // 초기 설명 업데이트
    const buyTokenName = document.querySelector('#buy-token-name').textContent;
    const sellTokenName = document.querySelector('#sell-token-name').textContent;
    updateDescription(buyTokenName, sellTokenName);
};

// 글로벌 변수
let sellTokenPrice = 1; // "Sell" 토큰 가격
let buyTokenPrice = 1; // WemixDollar 가격 고정
