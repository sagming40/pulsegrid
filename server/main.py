from fastapi import FastAPI

# 매니저(app) 한 명 채용
# 이 app이 앞으로 모든 주소(엔드포인트)를 관리하게 됨
app = FastAPI()


# "/" 라는 주소로 GET 요청이 오면 이 함수를 실행해서 응답하라는 뜻
# 비유: 가게 정문에 "누가 왔나요?" 라고 물어보면 "네, 저 왔습니다." 라고 대답하는 것
@app.get("/")
def read_root():
    return {"message": "PulseGrid 서버가 살아있습니다 🚀"}
