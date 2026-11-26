from agent.react_loop import run_agent

if __name__ == "__main__":
    sonuc = run_agent("README.md dosyasını oku ve iki cümleyle özetle.")
    print("Agent cevabı:")
    print(sonuc)