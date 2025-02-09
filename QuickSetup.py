import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import threading
import os
import configparser
import requests
import zipfile

class PipInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoWSGR快速启动")
        self.venv_name = "autowsgr_venv"
        self.package_name = "autowsgr"
        self.config_file = "autowsgr_quicksetup_config.ini"
        self.examples_download_urls = {
            "GitHub": "https://github.com/OpenWSGR/AutoWSGR-examples/archive/refs/heads/main.zip",
            "moeyy加速": "https://github.moeyy.xyz/https://github.com/OpenWSGR/AutoWSGR-examples/archive/refs/heads/main.zip"
        }

        self.load_config()

        self.create_widgets()

    def load_config(self):
        """加载配置文件"""
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.config["DEFAULT"] = {
                "working_directory": "",
                "mirror_source": "默认",
                "examples_source": "GitHub"
            }
            self.save_config()

    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)
    
    def save_mirror_config(self, event=None):
        """保存镜像源配置"""
        selected_mirror = self.mirror_var.get()
        self.config["DEFAULT"]["mirror_source"] = selected_mirror
        self.save_config()
        self.output_area.insert(tk.END, f"镜像源已设置为: {selected_mirror}\n")

    def save_examples_source_config(self, event=None):
        """保存用例下载源配置"""
        selected_source = self.examples_source_var.get()
        self.config["DEFAULT"]["examples_source"] = selected_source
        self.save_config()
        self.output_area.insert(tk.END, f"用例下载源已设置为: {selected_source}\n")

    def create_widgets(self):
        # 工作目录选择
        ttk.Label(self.root, text="工作目录:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.path_var = tk.StringVar(value=self.config["DEFAULT"].get("working_directory", ""))
        self.path_entry = ttk.Entry(self.root, textvariable=self.path_var, width=40)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.root, text="选择目录", command=self.select_directory).grid(row=0, column=2, padx=5, pady=5)

        # 镜像源选择
        ttk.Label(self.root, text="镜像源:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.mirror_var = tk.StringVar(value=self.config["DEFAULT"].get("mirror_source", "默认"))
        self.mirror_combobox = ttk.Combobox(self.root, textvariable=self.mirror_var, 
                                         values=["默认", "阿里云", "清华大学"], width=15)
        self.mirror_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.mirror_combobox.bind("<<ComboboxSelected>>", self.save_mirror_config)
        ttk.Button(self.root, text="安装", command=self.install_package).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(self.root, text="更新", command=self.update_package).grid(row=1, column=3, padx=5, pady=5)

        # 用例下载
        ttk.Label(self.root, text="用例下载:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.examples_source_var = tk.StringVar(value=self.config["DEFAULT"].get("examples_source", "GitHub"))
        self.examples_source_combobox = ttk.Combobox(self.root, textvariable=self.examples_source_var, 
                                                   values=["GitHub", "moeyy加速"], width=15)
        self.examples_source_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.examples_source_combobox.bind("<<ComboboxSelected>>", self.save_examples_source_config)
        ttk.Button(self.root, text="下载", command=self.download_examples).grid(row=2, column=2, padx=5, pady=5)

        # 输出窗口
        self.output_area = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.output_area.grid(row=3, column=0, columnspan=4, padx=5, pady=5)

        ttk.Button(self.root, text="清空输出", command=self.clear_output_area).grid(row=4, column=0, padx=5, pady=5)
        
    def select_directory(self):
        """选择工作目录"""
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.path_var.set(selected_path)
            self.output_area.insert(tk.END, f"工作目录已设置为: {selected_path}\n")
            self.config["DEFAULT"]["working_directory"] = selected_path
            self.save_config()
            self.setup_venv()

    def clear_output_area(self):
        self.output_area.destroy()
        self.output_area = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.output_area.grid(row=3, column=0, columnspan=4, padx=5, pady=5)

    def download_examples(self):
        """下载并解压用例文件"""
        working_dir = self.path_var.get()
        if not working_dir:
            messagebox.showwarning("警告", "请先选择工作目录")
            return

        selected_source = self.examples_source_var.get()
        download_url = self.examples_download_urls.get(selected_source)
        if not download_url:
            messagebox.showerror("错误", "无效的下载源")
            return

        def download_and_extract():
            try:
                self.output_area.insert(tk.END, f"正在从 {selected_source} 下载用例文件...\n")
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                zip_path = os.path.join(working_dir, "examples.zip")
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # 解压文件
                self.output_area.insert(tk.END, "正在解压文件...\n")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(working_dir)

                # 删除zip文件
                os.remove(zip_path)
                self.output_area.insert(tk.END, "用例下载并解压完成！\n")
                messagebox.showinfo("成功", "用例下载并解压完成！")
            except Exception as e:
                self.output_area.insert(tk.END, f"下载或解压失败: {str(e)}\n")
                messagebox.showerror("错误", f"下载或解压失败: {str(e)}")

        threading.Thread(target=download_and_extract, daemon=True).start()

    def run_command(self, command, venv_activate=False):
        """在子线程中执行命令并捕获输出"""
        def run():
            try:
                working_dir = self.path_var.get()
                if not working_dir:
                    messagebox.showwarning("警告", "请先选择工作目录")
                    return

                if venv_activate:
                    venv_path = os.path.join(working_dir, self.venv_name)
                    if os.name == "nt":  # Windows系统
                        activate_script = os.path.join(venv_path, "Scripts", "activate")
                        full_command = f"call {activate_script} && {command}"
                    else:  # Linux/Mac系统
                        activate_script = os.path.join(venv_path, "bin", "activate")
                        full_command = f"source {activate_script} && {command}"
                else:
                    full_command = command

                process = subprocess.Popen(
                    full_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    universal_newlines=True,
                    cwd=working_dir
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.output_area.insert(tk.END, output)
                        self.output_area.see(tk.END)
                        
                return_code = process.poll()
                if return_code == 0:
                    messagebox.showinfo("成功", "操作执行成功！")
                else:
                    messagebox.showerror("错误", f"操作失败，返回码：{return_code}")
            
            except Exception as e:
                messagebox.showerror("异常", f"发生错误：{str(e)}")
        
        threading.Thread(target=run, daemon=True).start()

    def get_mirror_options(self, action="install"):
        """根据选择的镜像源生成pip选项"""
        mirror = self.mirror_var.get()
        options = []
        
        if mirror == "阿里云":
            options = [
                "-i", "https://mirrors.aliyun.com/pypi/simple",
                "--trusted-host", "mirrors.aliyun.com"
            ]
        elif mirror == "清华大学":
            options = [
                "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
                "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
            ]
        
        if action == "update" and mirror != "默认":
            options.append("--upgrade")
        
        return options

    def setup_venv(self):
        """检查并创建虚拟环境"""
        working_dir = self.path_var.get()
        if not working_dir:
            messagebox.showwarning("警告", "请先选择工作目录")
            return False

        venv_path = os.path.join(working_dir, self.venv_name)
        if not os.path.exists(venv_path):
            self.output_area.insert(tk.END, f"正在创建虚拟环境 '{venv_path}'...\n")
            self.run_command(f"python -m venv {self.venv_name}")
            return True
        return False

    def install_package(self):
        """安装包"""
        mirror_options = self.get_mirror_options()
        command = f"pip install {self.package_name} " + " ".join(mirror_options)
        self.run_command(command, venv_activate=True)

    def update_package(self):
        """更新包"""
        working_dir = self.path_var.get()
        if not working_dir:
            messagebox.showwarning("警告", "请先选择工作目录")
            return

        venv_path = os.path.join(working_dir, self.venv_name)
        if not os.path.exists(venv_path):
            messagebox.showwarning("警告", f"虚拟环境 '{venv_path}' 不存在，请先安装")
            return
        
        mirror_options = self.get_mirror_options("update")
        command = f"pip install --upgrade {self.package_name} " + " ".join(mirror_options)
        self.run_command(command, venv_activate=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = PipInstallerApp(root)
    root.mainloop()