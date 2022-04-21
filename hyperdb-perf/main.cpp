#include <cpr/cpr.h>
#include <sstream>
#include <gflags/gflags.h>
#include <memory>
#include <atomic>
#include <thread>
#include <chrono>
#include <vector>
#include <tabulate/table.hpp>
#include "utils.hpp"


DEFINE_string(ip, "10.25.127.19", "Server IP to send request to");
DEFINE_string(port, "5000", "Server port to send request to");
DEFINE_int32(time, 10, "Time to run the test");
DEFINE_int32(time_interval, 1, "Time interval between printing stats");
DEFINE_int32(get_threads, 1, "Number of threads to use");
DEFINE_int32(set_threads, 1, "Number of threads to use");


std::shared_ptr<std::string> get_url(nullptr);
std::shared_ptr<std::string> set_url(nullptr);

std::atomic<int> num_requests_sent(0);
std::atomic<int> num_requests_received(0);
bool run = false;

std::atomic<int> id(1);
std::vector<std::thread> threads;

int init() {
    if (FLAGS_ip.empty() || FLAGS_port.empty()) {
        LOG(ERROR) << "IP and Port is required";
        return 1;
    }

    if (FLAGS_time <= 0 || FLAGS_time_interval <= 0) {
        LOG(ERROR) << "Time must be greater than 0";
        return 1;
    }

    if (FLAGS_get_threads < 0 || FLAGS_set_threads < 0) {
        LOG(ERROR) << "Number of get threads must be greater than or equal to 0";
        return 1;
    }

    get_url = std::make_shared<std::string>("http://" + FLAGS_ip + ":" + FLAGS_port + "/api/v1/get_data/");
    set_url = std::make_shared<std::string>("http://" + FLAGS_ip + ":" + FLAGS_port + "/api/v1/insert/?height=1");

    return 0;
}

// Function get_data
// Description: Perform get opration to get the data from the API.
int get_data() {
    while(!run) {}
    while(run) {
        auto r = cpr::Get(cpr::Url{*get_url},
                cpr::Header{{"Content-Type", "application/json"}},
                cpr::Parameters{{"table", "diva@testnet.ustb.edu"}}
                );
        if (r.status_code < 200 || r.status_code >= 300) {
            LOG(ERROR) << "Failed to get data from server: " << r.status_code;
            return -1;
        }
        num_requests_received++;
        // std::cout << r.text << std::endl;
    }
    return 0;
}

int insert_data() {
    std::ostringstream oss;

    oss << "{\"id\":\"" << id << "\",\"name\":\"" << random_string() << "\",\"experiment_time\":\"1648113899\",\"author\":\"maning\",\"email\":\"maning@gmail.com\",\"institution\":\"UESTC\",\"environment\":\"sfghghh\",\"parameters\":\"as=js\",\"details\":\"\u5b9e\u9a8c\u505a\u4e86\u4ec0\u4e48\",\"attachment\":\"https://www.ustb.edu.cn\"}";
    std::string str = oss.str();
    while(!run) {}
    while (run) {
        auto r = cpr::Post(cpr::Url{*set_url},
                cpr::Header{{"Content-Type", "application/json"}},
                cpr::Body{str}
                );

        if (r.status_code < 200 || r.status_code >= 300) {
            LOG(ERROR) << "Failed to insert data to server: " << r.status_code;
            return -1;
        }
        num_requests_sent++;
        id++;
    }
    return 0;
}

void printing_thread() {
    time_t start_time = time(NULL);

    
    while(time(NULL) - start_time < FLAGS_time) {
        int64_t t1 = std::chrono::duration_cast<std::chrono::milliseconds> (
            std::chrono::system_clock::now().time_since_epoch()
            ).count();
        std::this_thread::sleep_for(std::chrono::seconds(FLAGS_time_interval));
        static int pre_set_count = 0;
        static int pre_get_count = 0;

        int set_count = num_requests_sent.load() - pre_set_count;
        int get_count = num_requests_received.load() - pre_get_count;
        int64_t t2 = std::chrono::duration_cast<std::chrono::milliseconds> (
                std::chrono::system_clock::now().time_since_epoch()
                ).count();

        tabulate::Table table;
        auto time_diff = static_cast<double>(t2 - t1);
        table.add_row({"Set count", "Get count", "Set qps", "Get qps", "Total qps", "Set lat", "Get lat"});
        table.add_row({std::to_string(set_count), std::to_string(get_count), std::to_string(set_count / FLAGS_time_interval), 
                std::to_string(get_count / FLAGS_time_interval), std::to_string((set_count + get_count) / FLAGS_time_interval),
                set_count == 0 ? "0" : std::to_string(time_diff / static_cast<double>(set_count)), 
                get_count == 0 ? "0" : std::to_string(time_diff/static_cast<double>(get_count))});

        table[0][0].format().font_color(tabulate::Color::yellow);
        table[0][1].format().font_color(tabulate::Color::yellow);
        table[0][2].format().font_color(tabulate::Color::yellow);
        table[0][3].format().font_color(tabulate::Color::yellow);
        table[0][4].format().font_color(tabulate::Color::yellow);
        table[0][5].format().font_color(tabulate::Color::yellow);
        table[0][6].format().font_color(tabulate::Color::yellow);
        std::cout << table << std::endl;

        pre_set_count += set_count;
        pre_get_count += get_count;

    }
    run = false;
}

void start_testing() {

    for (int i = 0; i < FLAGS_get_threads; i++) {
        threads.emplace_back(std::thread(get_data));
    }

    for (int i = 0; i < FLAGS_set_threads; i++) {
        threads.emplace_back(std::thread(insert_data));
    }
    
    threads.emplace_back(std::thread(printing_thread));
    run = true;
    for (auto& t : threads) {
        t.join();
    }
}

int main(int argc, char* argv[]) {
    gflags::ParseCommandLineFlags(&argc, &argv, true);
    init();
    google::InitGoogleLogging(argv[0]);
    start_testing();
    return 0;
}
