#!/usr/bin/env python3
"""
RAGFlow文件批量上传脚本

功能：将指定目录下的所有文件上传到RAGFlow的指定知识库中，并记录详细的日志

使用方法：
python ragflow_uploader.py --api_key YOUR_API_KEY --base_url http://your_ragflow_url:9380 --dataset_name your_dataset_name --directory /path/to/files

日志记录：
- 自动生成时间戳命名的日志文件，也可通过 --log_file 参数指定
- 记录每个文件的上传状态、耗时统计和详细的错误信息
- 控制台显示主要进度，日志文件包含完整的调试信息

依赖安装：
pip install ragflow-sdk loguru
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from ragflow_sdk import RAGFlow
from loguru import logger


class RAGFlowUploader:
    """RAGFlow文件上传器"""
    
    def __init__(self, api_key, base_url, log_file=None):
        """
        初始化RAGFlow连接
        
        Args:
            api_key (str): RAGFlow API密钥
            base_url (str): RAGFlow服务器地址
            log_file (str): 日志文件路径，如果为None则自动生成
        """
        # 配置日志
        self._setup_logger(log_file)
        
        self.rag = RAGFlow(api_key=api_key, base_url=base_url)
        logger.info(f"已连接到RAGFlow服务器：{base_url}")
    
    def _setup_logger(self, log_file=None):
        """
        设置loguru日志配置
        
        Args:
            log_file (str): 日志文件路径
        """
        # 移除默认的控制台处理器
        logger.remove()
        
        # 添加控制台处理器（仅显示INFO及以上级别）
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            colorize=True
        )
        
        # 设置日志文件路径
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"ragflow_upload_{timestamp}.log"
        
        # 添加文件处理器（记录所有级别）
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8"
        )
        
        logger.info(f"日志文件已设置：{log_file}")
    
    def get_or_create_dataset(self, dataset_name):
        """
        获取或创建知识库
        
        Args:
            dataset_name (str): 知识库名称
            
        Returns:
            DataSet: 知识库对象
        """
        logger.info(f"开始处理知识库：{dataset_name}")
        
        # 首先尝试查找现有的知识库
        try:
            logger.debug(f"正在查找现有知识库：{dataset_name}")
            datasets = self.rag.list_datasets(name=dataset_name)
            if datasets:
                logger.success(f"找到现有知识库：{dataset_name}")
                return datasets[0]
            else:
                logger.info(f"未找到名为 {dataset_name} 的知识库，将创建新的知识库")
        except Exception as e:
            logger.error(f"查找知识库时出错：{e}")
        
        # 如果没有找到，创建新的知识库
        try:
            logger.info(f"开始创建新知识库：{dataset_name}")
            dataset = self.rag.create_dataset(
                name=dataset_name,
                description=f"通过脚本自动创建的知识库：{dataset_name}",
                chunk_method="naive",  # 使用通用分块方法
                permission="me"
            )
            logger.success(f"成功创建知识库：{dataset_name}，ID：{dataset.id if hasattr(dataset, 'id') else 'Unknown'}")
            return dataset
        except Exception as e:
            logger.error(f"创建知识库失败：{e}")
            raise
    
    def get_existing_documents(self, dataset):
        """
        获取知识库中所有现有文档，建立文档名称映射
        
        Args:
            dataset: 知识库对象
            
        Returns:
            dict: 以文档名为键的现有文档字典
        """
        logger.info("开始获取知识库中的现有文档")
        existing_docs = {}
        page = 1
        page_size = 50  # 每页获取的文档数量
        
        try:
            while True:
                logger.debug(f"获取第 {page} 页文档，每页 {page_size} 个")
                
                # 获取当前页的文档列表
                try:
                    documents = dataset.list_documents(page=page, page_size=page_size)
                except TypeError:
                    # 如果API不支持分页参数，则直接获取所有文档
                    logger.debug("API不支持分页参数，直接获取所有文档")
                    documents = dataset.list_documents()
                    if documents:
                        for doc in documents:
                            doc_name = getattr(doc, 'name', getattr(doc, 'display_name', f'unknown_{doc.id}'))
                            existing_docs[doc_name] = doc
                            logger.debug(f"现有文档：{doc_name} (ID: {doc.id})")
                    break
                
                if not documents:
                    logger.debug(f"第 {page} 页无文档，结束获取")
                    break
                
                # 处理当前页的文档
                for doc in documents:
                    # 尝试获取文档名称，优先使用name，其次display_name，最后使用ID
                    doc_name = getattr(doc, 'name', getattr(doc, 'display_name', f'unknown_{doc.id}'))
                    existing_docs[doc_name] = doc
                    logger.debug(f"现有文档：{doc_name} (ID: {doc.id})")
                
                # 如果当前页文档数量少于page_size，说明已经是最后一页
                if len(documents) < page_size:
                    logger.debug(f"第 {page} 页文档数量({len(documents)})少于页大小({page_size})，已到最后一页")
                    break
                
                page += 1
                
                # 安全检查，防止无限循环
                if page > 1000:  # 假设最多不超过1000页
                    logger.warning("已达到最大页数限制(1000页)，停止获取")
                    break
            
            logger.info(f"成功获取 {len(existing_docs)} 个现有文档")
            
            # 如果文档数量不多，记录所有文档名
            if len(existing_docs) <= 20:
                logger.info("现有文档列表：")
                for doc_name in existing_docs.keys():
                    logger.info(f"  - {doc_name}")
            else:
                logger.info(f"现有文档较多({len(existing_docs)}个)，不在日志中详细列出")
            
            return existing_docs
            
        except Exception as e:
            logger.error(f"获取现有文档失败：{e}")
            # 如果获取失败，返回空字典，不影响后续上传流程
            return {}
    
    def is_supported_file(self, file_path):
        """
        检查文件是否为支持的格式
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否支持该文件格式
        """
        # 支持的文件扩展名
        supported_extensions = {
            '.txt', '.md', '.pdf', '.doc', '.docx', 
            '.ppt', '.pptx', '.xls', '.xlsx', '.csv',
            '.html', '.htm', '.json', '.xml', '.rtf'
        }
        
        file_ext = Path(file_path).suffix.lower()
        return file_ext in supported_extensions
    
    def get_files_from_directory(self, directory):
        """
        获取目录下所有支持的文件
        
        Args:
            directory (str): 目录路径
            
        Returns:
            list: 文件路径列表
        """
        logger.info(f"开始扫描目录：{directory}")
        
        directory = Path(directory)
        if not directory.exists():
            logger.error(f"目录不存在：{directory}")
            raise FileNotFoundError(f"目录不存在：{directory}")
        
        if not directory.is_dir():
            logger.error(f"路径不是目录：{directory}")
            raise NotADirectoryError(f"路径不是目录：{directory}")
        
        files = []
        total_files_scanned = 0
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_files_scanned += 1
                if self.is_supported_file(file_path):
                    files.append(file_path)
                    logger.debug(f"找到支持的文件：{file_path}")
                else:
                    logger.debug(f"跳过不支持的文件：{file_path}")
        
        logger.info(f"目录扫描完成：扫描了 {total_files_scanned} 个文件，找到 {len(files)} 个支持的文件")
        
        # 记录文件列表（如果文件数量不多的话）
        if len(files) <= 50:
            for file_path in files:
                logger.debug(f"待上传文件：{file_path}")
        else:
            logger.info(f"文件数量较多（{len(files)}个），不在日志中详细列出所有文件")
        
        return files
    
    def upload_files(self, dataset, file_paths, batch_size=5, skip_existing=False):
        """
        批量上传文件到知识库
        
        Args:
            dataset: 知识库对象
            file_paths (list): 文件路径列表
            batch_size (int): 每批上传的文件数量
            skip_existing (bool): 是否跳过已存在的文件
        """
        total_files = len(file_paths)
        successful_uploads = 0
        failed_uploads = []
        skipped_files = []
        upload_start_time = datetime.now()
        
        logger.info(f"开始上传任务：总共 {total_files} 个文件，批次大小：{batch_size}，跳过重复：{skip_existing}")
        
        # 如果需要跳过已存在的文件，先获取现有文档列表
        existing_docs = {}
        if skip_existing:
            existing_docs = self.get_existing_documents(dataset)
            if existing_docs:
                logger.info(f"获取到 {len(existing_docs)} 个现有文档，将跳过重复文件")
        
        # 过滤需要上传的文件
        files_to_upload = []
        for file_path in file_paths:
            file_name = file_path.name
            if skip_existing and file_name in existing_docs:
                skipped_files.append(str(file_path))
                logger.info(f"跳过已存在的文件：{file_name}")
            else:
                files_to_upload.append(file_path)
        
        if skipped_files:
            logger.info(f"跳过 {len(skipped_files)} 个已存在的文件，实际需要上传 {len(files_to_upload)} 个文件")
        
        if not files_to_upload:
            logger.info("没有需要上传的新文件")
            return
        
        # 分批上传文件
        for i in range(0, len(files_to_upload), batch_size):
            batch_num = i // batch_size + 1
            batch_files = files_to_upload[i:i + batch_size]
            batch_documents = []
            
            logger.info(f"开始处理批次 {batch_num}：{len(batch_files)} 个文件")
            
            # 准备本批次的文件数据
            for file_path in batch_files:
                try:
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    document = {
                        'display_name': file_path.name,
                        'blob': file_content
                    }
                    batch_documents.append(document)
                    
                    file_size_mb = len(file_content) / (1024 * 1024)
                    logger.debug(f"文件准备就绪：{file_path.name} ({file_size_mb:.2f} MB)")
                    
                except Exception as e:
                    logger.error(f"读取文件失败：{file_path} - {e}")
                    print(f"读取文件 {file_path} 失败：{e}")
                    failed_uploads.append(str(file_path))
                    continue
            
            # 上传本批次文件
            if batch_documents:
                try:
                    batch_start_time = datetime.now()
                    logger.info(f"开始上传批次 {batch_num}：{len(batch_documents)} 个文件")
                    
                    dataset.upload_documents(batch_documents)
                    
                    batch_end_time = datetime.now()
                    batch_duration = (batch_end_time - batch_start_time).total_seconds()
                    
                    successful_uploads += len(batch_documents)
                    
                    # 记录每个成功上传的文件
                    for doc in batch_documents:
                        logger.success(f"文件上传成功：{doc['display_name']}")
                    
                    logger.success(f"批次 {batch_num} 上传成功：{len(batch_documents)} 个文件，耗时 {batch_duration:.2f} 秒")
                    print(f"成功上传批次 {batch_num}：{len(batch_documents)} 个文件")
                    
                except Exception as e:
                    logger.error(f"批次 {batch_num} 上传失败：{e}")
                    print(f"上传批次 {batch_num} 失败：{e}")
                    
                    # 记录失败的文件
                    for doc in batch_documents:
                        failed_uploads.append(doc['display_name'])
                        logger.error(f"文件上传失败：{doc['display_name']}")
        
        # 计算总耗时
        upload_end_time = datetime.now()
        total_duration = (upload_end_time - upload_start_time).total_seconds()
        
        # 输出上传结果统计
        logger.info("="*50)
        logger.info("上传任务完成统计")
        logger.info(f"总文件数：{total_files}")
        if skipped_files:
            logger.info(f"跳过重复：{len(skipped_files)} 个文件")
        logger.info(f"实际上传：{len(files_to_upload)} 个文件")
        logger.info(f"成功上传：{successful_uploads} 个文件")
        logger.info(f"上传失败：{len(failed_uploads)} 个文件")
        logger.info(f"总耗时：{total_duration:.2f} 秒")
        if len(files_to_upload) > 0:
            logger.info(f"平均每个文件耗时：{total_duration/len(files_to_upload):.2f} 秒")
        else:
            logger.info("平均耗时：0 秒")
        logger.info("="*50)
        
        print(f"\n上传完成！")
        if skipped_files:
            print(f"跳过重复：{len(skipped_files)} 个文件")
        print(f"成功上传：{successful_uploads} 个文件")
        if failed_uploads:
            print(f"上传失败：{len(failed_uploads)} 个文件")
            logger.warning("上传失败的文件列表：")
            print("失败的文件列表：")
            for failed_file in failed_uploads:
                logger.error(f"失败文件：{failed_file}")
                print(f"  - {failed_file}")
        
        # 如果有跳过的文件，也记录到日志中
        if skipped_files:
            logger.info("跳过的重复文件列表：")
            for skipped_file in skipped_files:
                logger.info(f"跳过文件：{skipped_file}")
    
    def start_parsing(self, dataset):
        """
        启动文档解析
        
        Args:
            dataset: 知识库对象
        """
        logger.info("开始启动文档解析")
        
        try:
            # 获取所有文档
            logger.debug("获取知识库中的所有文档")
            documents = dataset.list_documents()
            
            if not documents:
                logger.warning("知识库中没有文档需要解析")
                print("知识库中没有文档需要解析")
                return
            
            # 收集所有文档ID
            doc_ids = [doc.id for doc in documents]
            logger.info(f"找到 {len(doc_ids)} 个文档需要解析")
            
            # 记录文档详情
            for doc in documents:
                logger.debug(f"待解析文档：{doc.name if hasattr(doc, 'name') else 'Unknown'} (ID: {doc.id})")
            
            # 启动异步解析
            logger.info(f"开始启动异步解析：{len(doc_ids)} 个文档")
            print(f"开始解析 {len(doc_ids)} 个文档...")
            
            dataset.async_parse_documents(doc_ids)
            
            logger.success(f"文档解析已成功启动，共 {len(doc_ids)} 个文档")
            print("文档解析已启动，这可能需要一些时间完成")
            
        except Exception as e:
            logger.error(f"启动文档解析失败：{e}")
            print(f"启动文档解析失败：{e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将指定目录下的所有文件上传到RAGFlow知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python ragflow_uploader.py --api_key "your-api-key" --base_url "http://localhost:9380" --dataset_name "my_knowledge_base" --directory "/path/to/documents"
  
  python ragflow_uploader.py --api_key "your-api-key" --base_url "http://localhost:9380" --dataset_name "my_knowledge_base" --directory "/path/to/documents" --batch_size 3 --no_parse
        """
    )
    
    parser.add_argument(
        '--api_key',
        required=True,
        help='RAGFlow API密钥'
    )
    
    parser.add_argument(
        '--base_url',
        required=True,
        help='RAGFlow服务器地址 (例如: http://localhost:9380)'
    )
    
    parser.add_argument(
        '--dataset_name',
        required=True,
        help='知识库名称（如果不存在将自动创建）'
    )
    
    parser.add_argument(
        '--directory',
        required=True,
        help='要上传文件的目录路径'
    )
    
    parser.add_argument(
        '--batch_size',
        type=int,
        default=5,
        help='每批上传的文件数量（默认：5）'
    )
    
    parser.add_argument(
        '--no_parse',
        action='store_true',
        help='上传后不自动启动文档解析'
    )

    parser.add_argument(
        "--skip_existing",
        action='store_true',
        
    )
    
    parser.add_argument(
        '--log_file',
        help='指定日志文件路径（如果不指定，将自动生成时间戳命名的日志文件）'
    )
    
    args = parser.parse_args()
    
    # 记录程序开始时间
    program_start_time = datetime.now()
    
    try:
        # 创建上传器实例
        uploader = RAGFlowUploader(args.api_key, args.base_url, args.log_file)
        
        # 记录程序参数
        logger.info("程序启动参数：")
        logger.info(f"  API密钥：{'*' * (len(args.api_key) - 8) + args.api_key[-4:] if len(args.api_key) > 8 else '****'}")
        logger.info(f"  服务器地址：{args.base_url}")
        logger.info(f"  知识库名称：{args.dataset_name}")
        logger.info(f"  目录路径：{args.directory}")
        logger.info(f"  批次大小：{args.batch_size}")
        logger.info(f"  自动解析：{'否' if args.no_parse else '是'}")
        logger.info(f"  日志文件：{args.log_file or '自动生成'}")
        
        # 获取或创建知识库
        dataset = uploader.get_or_create_dataset(args.dataset_name)
        
        # 获取目录下的所有文件
        file_paths = uploader.get_files_from_directory(args.directory)
        
        if not file_paths:
            logger.warning("在指定目录中没有找到支持的文件")
            print("在指定目录中没有找到支持的文件")
            return
        
        # 上传文件
        uploader.upload_files(dataset, file_paths, args.batch_size, args.skip_existing)
        
        # 启动解析（如果需要）
        if not args.no_parse:
            uploader.start_parsing(dataset)
        else:
            logger.info("用户选择跳过自动解析")
            print("跳过自动解析，您可以稍后在RAGFlow界面中手动启动解析")
        
        # 计算总执行时间
        program_end_time = datetime.now()
        total_execution_time = (program_end_time - program_start_time).total_seconds()
        
        logger.success(f"脚本执行完成！总耗时：{total_execution_time:.2f} 秒")
        print("\n脚本执行完成！")
        
    except KeyboardInterrupt:
        logger.warning("用户中断了操作")
        print("\n用户中断了操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行过程中出现错误：{e}")
        print(f"\n执行过程中出现错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
