from implementation_logger import(
    create_implementation_log,
    add_log_entry,
    save_implementation_log
)

def main():
    log_data = create_implementation_log(
        task="hello.pyを作成する",
        repo_path="harness-test",
    branch_name="agent/task-test"
    )

    add_log_entry(
        log_data=log_data,
        attempt=1,
        test_passed=True,
        test_output="Hello from AI",
        review_passed=True,
        review="問題なし\nVERDICT: PASS",
        repair_attempted=False
    )

    log_path = save_implementation_log(
        log_data=log_data,
        status="SUCCESS"
    )

    print("ログ保存成功！")
    print(f"保存先: {log_path}")

if __name__ == "__main__":
    main()